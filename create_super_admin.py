from db.database import SessionLocal
from db.models import User
from app.auth import get_password_hash

def create_super_admin():
    db = SessionLocal()
    try:
        # Controlla se esiste già un AS
        existing_as = db.query(User).filter(User.role == "AS").first()
        if existing_as:
            print("Un Amministratore Supremo (AS) esiste già!")
            return
            
        # Crea il nuovo AS
        super_admin = User(
            email="admin@supremo.com",
            hashed_password=get_password_hash("password_suprema"),
            role="AS",
            tenant_id=None  # L'AS non appartiene a nessun tenant
        )
        db.add(super_admin)
        db.commit()
        print("Amministratore Supremo (AS) creato con successo!")
        print("Email: admin@supremo.com")
        print("Password: password_suprema")
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()
