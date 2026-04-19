from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from db.database import get_db
from app.schemas import PointModifierCreate, PointModifierResponse, MatchdayCalculate, MatchResponse, LineupCreate, LineupResponse
from app.auth import require_role
from app.crud import create_point_modifier, generate_calendar, calculate_matchday, submit_lineup
from db.models import Match, Lineup, Team

router = APIRouter(prefix="/matches", tags=["matches"])

@router.post("/modifiers", response_model=PointModifierResponse)
def add_modifier(mod_in: PointModifierCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["TA"]))):
    """
    Crea un modificatore (bonus/malus).
    """
    return create_point_modifier(db=db, mod_in=mod_in, tenant_id=current_user.tenant_id)

@router.post("/generate-calendar")
def create_calendar(team_ids: List[int], total_matchdays: int, db: Session = Depends(get_db), current_user = Depends(require_role(["TA"]))):
    """
    Genera il calendario per il tenant.
    """
    generate_calendar(db=db, tenant_id=current_user.tenant_id, team_ids=team_ids, total_matchdays=total_matchdays)
    return {"message": "Calendario generato con successo"}

@router.post("/lineups/{team_id}", response_model=LineupResponse)
def post_lineup(team_id: int, lineup_data: LineupCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["TA", "TU"]))):
    """
    Schiera la formazione per una giornata.
    """
    return submit_lineup(db=db, team_id=team_id, tenant_id=current_user.tenant_id, lineup_data=lineup_data)

@router.post("/calculate")
def compute_matchday(data: MatchdayCalculate, db: Session = Depends(get_db), current_user = Depends(require_role(["TA"]))):
    """
    Calcola i punteggi della giornata.
    """
    return calculate_matchday(db=db, tenant_id=current_user.tenant_id, data=data)

@router.get("/", response_model=List[MatchResponse])
def get_matches(db: Session = Depends(get_db), current_user = Depends(require_role(["TA", "TU"]))):
    """
    Visualizza i match e i risultati.
    """
    return db.query(Match).filter(Match.tenant_id == current_user.tenant_id).order_by(Match.matchday).all()

@router.get("/lineups/{team_id}", response_model=LineupResponse)
def get_lineup(team_id: int, matchday: int, db: Session = Depends(get_db), current_user = Depends(require_role(["TA", "TU"]))):
    """
    Recupera la formazione schierata per una specifica squadra e giornata.
    """
    lineup = db.query(Lineup).join(Team).filter(
        Team.tenant_id == current_user.tenant_id,
        Lineup.team_id == team_id,
        Lineup.matchday == matchday
    ).first()
    if not lineup:
        raise HTTPException(status_code=404, detail="Formazione non trovata")
    return lineup
