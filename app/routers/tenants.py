from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from app.schemas import TenantCreate, TenantResponse
from app.auth import require_role
from app.crud import create_tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])

@router.post("/", response_model=TenantResponse)
def create_new_tenant(tenant_in: TenantCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["AS"]))):
    """
    Crea un nuovo Fantacalcio (Tenant) e l'amministratore (TA). Solo l'Amministratore Supremo (AS) può farlo.
    """
    return create_tenant(db=db, tenant_in=tenant_in)
