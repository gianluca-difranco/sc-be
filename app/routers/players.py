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

from fastapi import UploadFile, File, HTTPException
import csv
import io

@router.post("/import")
async def import_players_csv(file: UploadFile = File(...), db: Session = Depends(get_db), current_user = Depends(require_role(["TA"]))):
    """
    Importa giocatori da un file CSV.
    Il CSV deve avere le colonne: name, role, credits
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Il file deve essere un CSV")
        
    try:
        contents = await file.read()
        decoded = contents.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        
        ALLOWED_ROLES = {"P", "D", "C", "A"}
        imported_count = 0
        for row in reader:
            if 'name' in row and 'role' in row and 'credits' in row:
                role = row['role'].strip().upper()
                if role not in ALLOWED_ROLES:
                    raise ValueError(f"Ruolo '{role}' non valido per il giocatore {row['name']}. I ruoli ammessi sono: P, D, C, A.")
                
                player_in = PlayerCreate(
                    name=row['name'].strip(),
                    role=role,
                    credits=int(row['credits'].strip())
                )
                create_player(db=db, player_in=player_in, tenant_id=current_user.tenant_id)
                imported_count += 1
                
        return {"message": f"{imported_count} giocatori importati con successo"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Errore durante l'importazione: {str(e)}")
