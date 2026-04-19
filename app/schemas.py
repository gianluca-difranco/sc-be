from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[int] = None

class UserBase(BaseModel):
    email: str
    role: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    tenant_id: Optional[int] = None
    class Config:
        from_attributes = True

class TenantBase(BaseModel):
    name: str
    allow_duplicate_players: bool = False
    lineup_size: int = 11
    bench_size: int = 15
    role_constraints: Optional[Dict[str, int]] = None

class TenantCreate(TenantBase):
    admin_email: str
    admin_password: str

class TenantResponse(TenantBase):
    id: int
    class Config:
        from_attributes = True

class PlayerBase(BaseModel):
    name: str
    role: str
    credits: int

class PlayerCreate(PlayerBase):
    pass

class PlayerResponse(PlayerBase):
    id: int
    tenant_id: int
    class Config:
        from_attributes = True

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    owner_id: int

class TeamResponse(TeamBase):
    id: int
    tenant_id: int
    owner_id: int
    players: List[PlayerResponse] = []
    class Config:
        from_attributes = True

class StandingResponse(BaseModel):
    team_id: int
    team_name: str
    points: int
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: float
    goals_against: float
    
class PointModifierCreate(BaseModel):
    name: str
    display_name: str
    value: float

    @field_validator('value')
    def validate_half_points(cls, v):
        if (v * 2) % 1 != 0:
            raise ValueError("Il punteggio deve essere un multiplo di 0.5")
        return v

class PointModifierResponse(PointModifierCreate):
    id: int
    tenant_id: int
    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    id: int
    tenant_id: int
    matchday: int
    home_team_id: Optional[int]
    away_team_id: Optional[int]
    home_score: Optional[float]
    away_score: Optional[float]
    class Config:
        from_attributes = True

class LineupCreate(BaseModel):
    matchday: int
    player_ids: List[int]
    bench_ids: List[int]

class LineupResponse(LineupCreate):
    id: int
    team_id: int
    total_score: Optional[float]
    class Config:
        from_attributes = True

class PerformanceUpdate(BaseModel):
    base_score: float
    modifier_ids: List[int] = []

class MatchdayCalculate(BaseModel):
    matchday: int
    performances: Dict[int, PerformanceUpdate] # player_id -> performance