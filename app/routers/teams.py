from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from app.schemas import TeamCreate, TeamResponse, StandingResponse
from app.auth import require_role
from app.crud import create_team, add_player_to_team, get_standings
from db.models import Team

router = APIRouter(prefix="/teams", tags=["teams"])

@router.post("/", response_model=TeamResponse)
def add_team(team_in: TeamCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["TA"]))):
    """
    Crea una nuova squadra.
    """
    return create_team(db=db, team_in=team_in, tenant_id=current_user.tenant_id)

@router.post("/{team_id}/players/{player_id}", response_model=TeamResponse)
def assign_player(team_id: int, player_id: int, db: Session = Depends(get_db), current_user = Depends(require_role(["TA"]))):
    """
    Assegna un giocatore a una squadra.
    """
    return add_player_to_team(db=db, team_id=team_id, player_id=player_id, tenant_id=current_user.tenant_id)

@router.get("/", response_model=List[TeamResponse])
def get_teams(db: Session = Depends(get_db), current_user = Depends(require_role(["TA", "TU"]))):
    """
    Lista tutte le squadre del tenant.
    """
    return db.query(Team).filter(Team.tenant_id == current_user.tenant_id).all()

@router.get("/mine", response_model=TeamResponse)
def get_my_team(db: Session = Depends(get_db), current_user = Depends(require_role(["TA", "TU"]))):
    """
    Recupera la squadra posseduta dall'utente loggato.
    """
    team = db.query(Team).filter(
        Team.tenant_id == current_user.tenant_id,
        Team.owner_id == current_user.id
    ).first()
    if not team:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Nessuna squadra associata a questo utente")
    return team

@router.get("/standings", response_model=List[StandingResponse])
def get_tenant_standings(db: Session = Depends(get_db), current_user = Depends(require_role(["TA", "TU"]))):
    """
    Ottiene la classifica del tenant basata sulle giornate giocate.
    """
    return get_standings(db=db, tenant_id=current_user.tenant_id)
