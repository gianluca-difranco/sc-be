from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Config(BaseSettings):
    # Componenti per costruire la URL (usati in produzione/ECS)
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: str = "5432"
    DB_NAME: str = "projectdb"

    # URL completa (usata se fornita, altrimenti costruita dai componenti sopra)
    DATABASE_URL: Optional[str] = None
    
    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if all([self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_NAME]):
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        # Default per sviluppo locale
        return "postgresql://postgres:mypassword@localhost:5432/projectdb"

    SECRET_KEY: str = "CAMBIAMI_IN_PRODUZIONE"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Costanti di Business
    MIN_LINEUP: int = 2
    MAX_LINEUP: int = 11
    POINT_STEP: float = 0.5
    MAX_BENCH_SIZE: int = 15

    # AWS SQS / SNS
    AWS_REGION: str = "eu-south-1"
    SQS_QUEUE_URL: str = ""  # Es: https://sqs.eu-west-1.amazonaws.com/123456789/my-queue
    SQS_MATCHDAY_QUEUE_URL: str = ""
    SNS_TOPIC_ARN: str = ""
    AWS_ENDPOINT_URL: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FRONTEND_URL: str = "http://localhost:5173"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config = Config()