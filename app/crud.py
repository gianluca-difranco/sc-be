import random
import string
from sqlalchemy.orm import Session
from fastapi import HTTPException
from db.models import Tenant, User, Player, Team, PointModifier, Match, Performance, Lineup
from app.schemas import TenantCreate, TenantUpdate, UserCreate, PlayerCreate, TeamCreate, PointModifierCreate, LineupCreate, MatchdayCalculate
from app.utils.sns import subscribe_user_to_tenant_topic
from app.utils.sqs import send_to_sqs
from core.config import config

def generate_tenant_code(db: Session) -> str:
    while True:
        letters = ''.join(random.choices(string.ascii_uppercase, k=5))
        numbers = ''.join(random.choices(string.digits, k=2))
        code = letters + numbers
        if not db.query(Tenant).filter(Tenant.code == code).first():
            return code

def create_tenant(db: Session, tenant_in: TenantCreate):
    code = generate_tenant_code(db)
    db_tenant = Tenant(
        name=tenant_in.name,
        code=code,
        allow_duplicate_players=tenant_in.allow_duplicate_players,
        lineup_size=tenant_in.lineup_size,
        bench_size=tenant_in.bench_size,
        role_constraints=tenant_in.role_constraints
    )
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    
    db_user = User(
        tenant_id=db_tenant.id,
        email=tenant_in.admin_email,
        hashed_password=None,
        role="TA"
    )
    db.add(db_user)
    db.commit()
    
    # Iscrivi il TA al topic SNS del tenant
    subscribe_user_to_tenant_topic(db_user.email, db_tenant.id)
    
    return db_tenant

def get_all_tenants(db: Session):
    return db.query(Tenant).all()

def update_tenant(db: Session, tenant_id: int, tenant_in: TenantUpdate):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trovato")
    update_data = tenant_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    db.commit()
    db.refresh(tenant)
    return tenant

def delete_tenant(db: Session, tenant_id: int):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trovato")
    
    # Cascata manuale: elimina tutti i dati collegati al tenant
    # Performance
    from db.models import Performance, Lineup, Match, PointModifier, Team, Player, User
    
    # Rimuove le associazioni team_players prima di eliminare squadre/giocatori
    teams = db.query(Team).filter(Team.tenant_id == tenant_id).all()
    for team in teams:
        team.players = []
    db.commit()
    
    # Lineups
    lineups = db.query(Lineup).join(Team).filter(Team.tenant_id == tenant_id).all()
    for lineup in lineups:
        db.delete(lineup)
    
    # Performances
    performances = db.query(Performance).filter(Performance.tenant_id == tenant_id).all()
    for perf in performances:
        perf.modifiers = []
    db.commit()
    for perf in performances:
        db.delete(perf)
    
    # Matches
    matches = db.query(Match).filter(Match.tenant_id == tenant_id).all()
    for match in matches:
        db.delete(match)
    
    # PointModifiers
    mods = db.query(PointModifier).filter(PointModifier.tenant_id == tenant_id).all()
    for mod in mods:
        db.delete(mod)
    
    # Players
    players = db.query(Player).filter(Player.tenant_id == tenant_id).all()
    for player in players:
        db.delete(player)
    
    # Teams
    for team in teams:
        db.delete(team)
    
    # Users del tenant
    users = db.query(User).filter(User.tenant_id == tenant_id).all()
    for user in users:
        db.delete(user)
    
    # Infine il tenant stesso
    db.delete(tenant)
    db.commit()
    return {"message": f"Tenant '{tenant.name}' eliminato con successo"}

def create_user(db: Session, user_in: UserCreate, tenant_id: int):
    db_user = User(
        tenant_id=tenant_id,
        email=user_in.email,
        hashed_password=None,
        role=user_in.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Iscrivi l'utente al topic SNS del tenant
    subscribe_user_to_tenant_topic(db_user.email, tenant_id)
    
    return db_user

def create_player(db: Session, player_in: PlayerCreate, tenant_id: int):
    db_player = Player(**player_in.model_dump(), tenant_id=tenant_id)
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player

def create_team(db: Session, team_in: TeamCreate, tenant_id: int):
    user = db.query(User).filter(User.email == team_in.owner_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    db_team = Team(name=team_in.name, owner_id=user.id, tenant_id=tenant_id)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

def add_player_to_team(db: Session, team_id: int, player_id: int, tenant_id: int):
    team = db.query(Team).filter(Team.id == team_id, Team.tenant_id == tenant_id).first()
    player = db.query(Player).filter(Player.id == player_id, Player.tenant_id == tenant_id).first()
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not team or not player:
        raise HTTPException(status_code=404, detail="Squadra o giocatore non trovati")
        
    if not tenant.allow_duplicate_players:
        if player.teams:
            raise HTTPException(status_code=400, detail="Il giocatore appartiene già ad un'altra squadra")
            
    team.players.append(player)
    db.commit()
    return team

def create_point_modifier(db: Session, mod_in: PointModifierCreate, tenant_id: int):
    db_mod = PointModifier(**mod_in.model_dump(), tenant_id=tenant_id)
    db.add(db_mod)
    db.commit()
    db.refresh(db_mod)
    return db_mod

def generate_calendar(db: Session, tenant_id: int, team_ids: list, total_matchdays: int):
    if len(team_ids) % 2 != 0:
        team_ids.append(None)

    n = len(team_ids)
    rounds = []
    teams = team_ids
    
    for i in range(n - 1):
        matches = []
        for j in range(n // 2):
            home, away = teams[j], teams[n - 1 - j]
            if home and away:
                matches.append((home, away))
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
        rounds.append(matches)

    for day in range(1, total_matchdays + 1):
        round_idx = (day - 1) % (n - 1)
        for h, a in rounds[round_idx]:
            new_match = Match(tenant_id=tenant_id, matchday=day, home_team_id=h, away_team_id=a)
            db.add(new_match)
    db.commit()

def validate_lineup(db: Session, tenant_id: int, lineup_data: LineupCreate):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if len(lineup_data.player_ids) != tenant.lineup_size:
        return False, f"Devi schierare esattamente {tenant.lineup_size} titolari"
    if len(lineup_data.bench_ids) > tenant.bench_size:
        return False, f"Massimo {tenant.bench_size} giocatori in panchina"
        
    if tenant.role_constraints:
        roles_in_lineup = {}
        for p_id in lineup_data.player_ids:
            player = db.query(Player).filter(Player.id == p_id).first()
            if not player: return False, f"Giocatore {p_id} non trovato"
            roles_in_lineup[player.role] = roles_in_lineup.get(player.role, 0) + 1
            
        for role, min_count in tenant.role_constraints.items():
            if roles_in_lineup.get(role, 0) < min_count:
                return False, f"Minimo {min_count} giocatori nel ruolo {role}"
    return True, "OK"

def submit_lineup(db: Session, team_id: int, tenant_id: int, lineup_data: LineupCreate):
    is_valid, msg = validate_lineup(db, tenant_id, lineup_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)
    
    lineup = db.query(Lineup).filter(Lineup.team_id == team_id, Lineup.matchday == lineup_data.matchday).first()
    if not lineup:
        lineup = Lineup(team_id=team_id, matchday=lineup_data.matchday)
        db.add(lineup)
    
    lineup.player_ids = lineup_data.player_ids
    lineup.bench_ids = lineup_data.bench_ids
    db.commit()
    db.refresh(lineup)
    return lineup

def calculate_matchday(db: Session, tenant_id: int, data: MatchdayCalculate):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    base_goal = tenant.base_score_for_goal if tenant.base_score_for_goal is not None else 66.0
    step_goal = tenant.step_for_goal if tenant.step_for_goal is not None else 6.0

    def calc_goals(score):
        if score is None or score < base_goal:
            return 0
        return int(1 + (score - base_goal) // step_goal)

    for p_id, perf_data in data.performances.items():
        perf = db.query(Performance).filter(
            Performance.player_id == p_id, 
            Performance.matchday == data.matchday,
            Performance.tenant_id == tenant_id
        ).first()
        if not perf:
            perf = Performance(player_id=p_id, matchday=data.matchday, tenant_id=tenant_id)
            db.add(perf)
        
        perf.base_score = perf_data.base_score
        perf.modifiers.clear()
        for mod_id in perf_data.modifier_ids:
            mod = db.query(PointModifier).filter(PointModifier.id == mod_id).first()
            if mod:
                perf.modifiers.append(mod)
    db.commit()

    lineups = db.query(Lineup).join(Team).filter(Team.tenant_id == tenant_id, Lineup.matchday == data.matchday).all()
    for lineup in lineups:
        score = 0.0
        available_bench = lineup.bench_ids.copy()
        
        for p_id in lineup.player_ids:
            perf = db.query(Performance).filter(Performance.player_id == p_id, Performance.matchday == data.matchday).first()
            if perf and perf.base_score > 0:
                p_score = perf.base_score + sum(m.value for m in perf.modifiers)
                score += p_score
            else:
                player = db.query(Player).filter(Player.id == p_id).first()
                subbed = False
                for bench_id in available_bench:
                    bench_player = db.query(Player).filter(Player.id == bench_id).first()
                    if bench_player.role == player.role:
                        b_perf = db.query(Performance).filter(Performance.player_id == bench_id, Performance.matchday == data.matchday).first()
                        if b_perf and b_perf.base_score > 0:
                            score += b_perf.base_score + sum(m.value for m in b_perf.modifiers)
                            available_bench.remove(bench_id)
                            subbed = True
                            break
                if not subbed:
                    score += 0
        lineup.total_score = score
        
        # update line matching lineup so it's persisted (it's bound to session)
    db.commit()
    
    matches = db.query(Match).filter(Match.tenant_id == tenant_id, Match.matchday == data.matchday).all()
    for match in matches:
        if match.home_team_id:
            h_lineup = db.query(Lineup).filter(Lineup.team_id == match.home_team_id, Lineup.matchday == data.matchday).first()
            match.home_score = calc_goals(h_lineup.total_score) if h_lineup else 0
        if match.away_team_id:
            a_lineup = db.query(Lineup).filter(Lineup.team_id == match.away_team_id, Lineup.matchday == data.matchday).first()
            match.away_score = calc_goals(a_lineup.total_score) if a_lineup else 0
    db.commit()
    
    results = []
    for m in matches:
        h_team = db.query(Team).filter(Team.id == m.home_team_id).first() if m.home_team_id else None
        a_team = db.query(Team).filter(Team.id == m.away_team_id).first() if m.away_team_id else None
        results.append({
            "home_team": h_team.name if h_team else "Riposo",
            "away_team": a_team.name if a_team else "Riposo",
            "home_score": m.home_score,
            "away_score": m.away_score
        })

    # Recupera le email degli utenti del tenant per la Lambda
    from db.models import User
    users = db.query(User).filter(User.tenant_id == tenant_id).all()
    emails = [u.email for u in users]

    # Invia messaggio a SQS per notificare la fine del calcolo
    sqs_payload = {
        "tenant_id": tenant_id,
        "matchday": data.matchday,
        "results": results,
        "emails": emails
    }
    send_to_sqs(sqs_payload, queue_url=config.SQS_MATCHDAY_QUEUE_URL)
    
    return {"message": "Giornata calcolata con successo"}

def get_standings(db: Session, tenant_id: int):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return []
    
    teams = db.query(Team).filter(Team.tenant_id == tenant_id).all()
    standings = {t.id: {"team_id": t.id, "team_name": t.name, "points": 0, "played": 0, "won": 0, "drawn": 0, "lost": 0, "goals_for": 0.0, "goals_against": 0.0} for t in teams}

    matches = db.query(Match).filter(Match.tenant_id == tenant_id).all()
    for match in matches:
        if match.home_score is not None and match.away_score is not None:
            if match.home_team_id in standings and match.away_team_id in standings:
                hs = match.home_score
                as_ = match.away_score
                
                standings[match.home_team_id]["played"] += 1
                standings[match.away_team_id]["played"] += 1
                standings[match.home_team_id]["goals_for"] += hs
                standings[match.home_team_id]["goals_against"] += as_
                standings[match.away_team_id]["goals_for"] += as_
                standings[match.away_team_id]["goals_against"] += hs
                
                if hs > as_:
                    standings[match.home_team_id]["points"] += 3
                    standings[match.home_team_id]["won"] += 1
                    standings[match.away_team_id]["lost"] += 1
                elif hs < as_:
                    standings[match.away_team_id]["points"] += 3
                    standings[match.away_team_id]["won"] += 1
                    standings[match.home_team_id]["lost"] += 1
                else:
                    standings[match.home_team_id]["points"] += 1
                    standings[match.away_team_id]["points"] += 1
                    standings[match.home_team_id]["drawn"] += 1
                    standings[match.away_team_id]["drawn"] += 1

    return sorted(list(standings.values()), key=lambda x: (x["points"], x["goals_for"]), reverse=True)