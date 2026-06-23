import os
from db.database import SessionLocal
from db.models import User
from app.auth import get_password_hash

def create_super_admin():
    db = SessionLocal()
    try:
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@supremo.com")
        admin_password = os.environ.get("ADMIN_PASSWORD", "password_suprema")

        # Controlla se esiste già un AS
        existing_as = db.query(User).filter(User.role == "AS", User.email == admin_email).first()
        if existing_as:
            print(f"L'Amministratore Supremo ({admin_email}) esiste già!")
            return
            
        # Crea il nuovo AS
        super_admin = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            role="AS",
            tenant_id=None  # L'AS non appartiene a nessun tenant
        )
        db.add(super_admin)
        db.commit()
        print(f"Amministratore Supremo (AS) creato con successo!")
        print(f"Email: {admin_email}")
        print("Password: <nascosta>")
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()
