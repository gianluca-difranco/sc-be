from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from app.schemas import PlayerCreate, PlayerResponse
from app.auth import require_role
from app.crud import create_player
from db.models import Player

router = APIRouter(prefix="/players", tags=["players"])

@router.post("/", response_model=PlayerResponse)
def add_player(player_in: PlayerCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["TA"]))):
    """ 
    Crea un nuovo calciatore nel sistema.
    """
    return create_player(db=db, player_in=player_in, tenant_id=current_user.tenant_id)

@router.get("/", response_model=List[PlayerResponse])
def get_players(db: Session = Depends(get_db), current_user = Depends(require_role(["TA", "TU"]))):
    """
    Lista tutti i calciatori del tenant.
    """
    return db.query(Player).filter(Player.tenant_id == current_user.tenant_id).all()
