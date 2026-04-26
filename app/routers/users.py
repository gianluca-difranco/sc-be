from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from app.schemas import UserCreate, UserResponse
from app.auth import require_role, create_access_token
from app.crud import create_user
from db.models import User
from app.utils.email import send_set_password_email

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
def create_tenant_user(user_in: UserCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["TA"]))):
    """
    Crea un nuovo utente (TU) nel tenant dell'amministratore.
    """
    user = create_user(db=db, user_in=user_in, tenant_id=current_user.tenant_id)
    token = create_access_token({"sub": user.email, "action": "set_password"})
    send_set_password_email(user.email, token)
    return user

@router.get("/", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db), current_user = Depends(require_role(["TA"]))):
    """
    Lista tutti gli utenti del tenant (solo per TA).
    """
    return db.query(User).filter(User.tenant_id == current_user.tenant_id).all()
