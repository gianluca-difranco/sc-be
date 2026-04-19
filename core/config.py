from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Config(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:mypassword@localhost:5432/projectdb"
    SECRET_KEY: str = "CAMBIAMI_IN_PRODUZIONE"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Costanti di Business
    MIN_LINEUP: int = 2
    MAX_LINEUP: int = 11
    POINT_STEP: float = 0.5
    MAX_BENCH_SIZE: int = 15
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config = Config()