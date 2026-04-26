from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from db.database import get_db
from app.auth import verify_password, create_access_token, get_password_hash
from app.schemas import Token, RegisterRequest, SetPasswordRequest, TenantCreate, UserCreate
from db.models import User, Tenant
from app.crud import create_tenant, create_user
from app.utils.email import send_set_password_email
from jose import jwt, JWTError
from core.config import config

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non validi",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "tenant_id": user.tenant_id}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    if req.fanta_name:
        # Create a new tenant and register as TA
        existing_tenant = db.query(Tenant).filter(Tenant.name == req.fanta_name).first()
        if existing_tenant:
            raise HTTPException(status_code=400, detail="Nome fantacalcio già in uso")
        
        tenant_in = TenantCreate(
            name=req.fanta_name,
            admin_email=req.email
        )
        tenant = create_tenant(db, tenant_in)
    elif req.fanta_code:
        # Join existing tenant as TU
        tenant = db.query(Tenant).filter(Tenant.code == req.fanta_code).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Fantacalcio non trovato con questo codice")
        
        user_in = UserCreate(
            email=req.email,
            role="TU"
        )
        create_user(db, user_in, tenant.id)
    else:
        raise HTTPException(status_code=400, detail="Devi fornire il nome del fantacalcio o il codice")

    # Generate token for password setup
    token = create_access_token({"sub": req.email, "action": "set_password"})
    send_set_password_email(req.email, token)
    return {"message": "Registrazione completata. Controlla la tua email per impostare la password."}

@router.post("/set-password")
def set_password(req: SetPasswordRequest, db: Session = Depends(get_db)):
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Le password non corrispondono")
        
    try:
        payload = jwt.decode(req.token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email: str = payload.get("sub")
        action: str = payload.get("action")
        if email is None or action != "set_password":
            raise HTTPException(status_code=400, detail="Token non valido")
    except JWTError:
        raise HTTPException(status_code=400, detail="Token scaduto o non valido")
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
        
    user.hashed_password = get_password_hash(req.new_password)
    db.commit()
    return {"message": "Password impostata con successo"}
