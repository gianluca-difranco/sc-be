from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from app.auth import require_role, get_password_hash
from db.models import PointModifier, Performance, Tenant, User


router = APIRouter()

@router.post("/calculate-scores/{matchday}")
def assign_player_points(matchday: int, player_id: int, modifier_ids: list[int], db: Session = Depends(get_db), current_user = Depends(require_role(["TA"]))):
    # Recupera i modificatori scelti dal TA
    mods = db.query(PointModifier).filter(PointModifier.id.in_(modifier_ids)).all()
    
    performance = Performance(
        player_id=player_id,
        matchday=matchday,
        tenant_id=current_user.tenant_id,
        modifiers=mods
    )
    db.add(performance)
    db.commit()
    return {"status": "Punteggio assegnato"}


@router.post("/create-tenant")
def create_new_fantacalcio(name: str, admin_email: str, db: Session = Depends(get_db), current_user = Depends(require_role(["AS"]))):
    # 1. Crea Tenant
    new_tenant = Tenant(name=name)
    db.add(new_tenant)
    db.flush() # Per avere l'ID
    
    # 2. Crea il primo TA
    new_ta = User(
        email=admin_email, 
        tenant_id=new_tenant.id, 
        role="TA",
        hashed_password=get_password_hash("password_temporanea")
    )
    db.add(new_ta)
    db.commit()
    return {"message": "Fantacalcio creato con successo"}