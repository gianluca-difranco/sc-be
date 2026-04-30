from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, JSON, Table
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

# Tabella di associazione per i voti presi dai calciatori in una giornata
performance_modifiers = Table(
    "performance_modifiers",
    Base.metadata,
    Column("performance_id", Integer, ForeignKey("performances.id")),
    Column("modifier_id", Integer, ForeignKey("point_modifiers.id"))
)

# Tabella di associazione per i giocatori nelle squadre
team_players = Table(
    "team_players",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("teams.id")),
    Column("player_id", Integer, ForeignKey("players.id"))
)

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    matchday = Column(Integer)  # Numero della giornata
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    home_score = Column(Float, nullable=True)
    away_score = Column(Float, nullable=True)

class Performance(Base):
    """Rappresenta il voto di un giocatore in una specifica giornata"""
    __tablename__ = "performances"
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    matchday = Column(Integer)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    base_score = Column(Float, default=0.0) # Voto base, 0 se non ha giocato
    modifiers = relationship("PointModifier", secondary=performance_modifiers)

class Lineup(Base):
    """La formazione schierata dall'utente"""
    __tablename__ = "lineups"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    matchday = Column(Integer)
    player_ids = Column(JSON) # Lista ID titolari, ordine importante
    bench_ids = Column(JSON)  # Lista ID panchina, ordine importante per subentri
    total_score = Column(Float, nullable=True)

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(7), unique=True, index=True, nullable=True) # 5 letters + 2 numbers
    name = Column(String, unique=True, nullable=False)
    # Regole del Tenant
    allow_duplicate_players = Column(Boolean, default=False)
    lineup_size = Column(Integer, default=5)
    bench_size = Column(Integer, default=5)
    role_constraints = Column(JSON, nullable=True) # Esempio: {"Portiere": 1, "Difensore": 3}
    base_score_for_goal = Column(Float, default=66.0) # Punteggio per il primo gol
    step_for_goal = Column(Float, default=6.0) # Punteggio per i gol successivi

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True) # Null se Supremo
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    role = Column(String) # AS, TA, TU

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    name = Column(String)
    role = Column(String)
    credits = Column(Integer)
    teams = relationship("Team", secondary=team_players, back_populates="players")

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    players = relationship("Player", secondary=team_players, back_populates="teams")

class PointModifier(Base):
    __tablename__ = "point_modifiers"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    name = Column(String)
    display_name = Column(String)
    value = Column(Float) # Step di 0.5 validati a livello applicativo