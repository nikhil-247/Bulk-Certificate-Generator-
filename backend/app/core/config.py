from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    app_name: str = "Bulk Certificate Generator"
    environment: str = "development"
    database_url: str = f"sqlite:///{BASE_DIR / 'certificate_generator.db'}"
    cors_origins: str = "http://localhost:5173"
    max_recipients: int = 5000
    storage_dir: str = str(STORAGE_DIR)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
