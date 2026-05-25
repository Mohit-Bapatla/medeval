from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    PROJECT_NAME: str = "MedEval"
    VERSION: str = "0.1.0-dev"
    API_V1_PREFIX: str = "/api/v1"
    EMBEDDING_DIMENSION: int = 384
    DEFAULT_EMBEDDING_MODEL: str = "deterministic-hash-embedding-384"
    DEFAULT_CHUNK_SIZE_CHARS: int = 1800
    DEFAULT_CHUNK_OVERLAP_CHARS: int = 250
    DEFAULT_MIN_CHUNK_CHARS: int = 200
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://medeval:medeval_dev_password@localhost:5432/medeval"
    )
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
