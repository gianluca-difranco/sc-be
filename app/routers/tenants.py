from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from db.models import Tenant
from app.schemas import TenantCreate, TenantResponse, TenantUpdate
from app.auth import require_role, create_access_token
from app.crud import create_tenant, get_all_tenants, delete_tenant, update_tenant
from app.utils.email import send_set_password_email

router = APIRouter(prefix="/tenants", tags=["tenants"])

@router.post("/", response_model=TenantResponse)
def create_new_tenant(
    tenant_in: TenantCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["AS"]))
):
    """
    Crea un nuovo Fantacalcio (Tenant) e l'amministratore (TA). Solo l'Amministratore Supremo (AS) può farlo.
    """
    tenant = create_tenant(db=db, tenant_in=tenant_in)
    token = create_access_token({"sub": tenant_in.admin_email, "action": "set_password"})
    send_set_password_email(tenant_in.admin_email, token)
    return tenant


@router.get("/", response_model=List[TenantResponse])
def list_tenants(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["AS"]))
):
    """
    Restituisce tutti i tenant attivi. Solo l'Amministratore Supremo (AS) può farlo.
    """
    return get_all_tenants(db=db)


@router.delete("/{tenant_id}")
def remove_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["AS"]))
):
    """
    Elimina un tenant e tutti i suoi dati (utenti, squadre, giocatori, partite, ecc.).
    Solo l'Amministratore Supremo (AS) può farlo.
    """
    return delete_tenant(db=db, tenant_id=tenant_id)

@router.get("/mine", response_model=TenantResponse)
def get_my_tenant(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["TA"]))
):
    """
    Restituisce le informazioni e impostazioni del tenant a cui appartiene il TA corrente.
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    return tenant

@router.put("/mine/settings", response_model=TenantResponse)
def update_my_tenant_settings(
    settings: TenantUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["TA"]))
):
    """
    Aggiorna le impostazioni del tenant (es. base_score_for_goal, step_for_goal). Solo TA.
    """
    return update_tenant(db=db, tenant_id=current_user.tenant_id, tenant_in=settings)
