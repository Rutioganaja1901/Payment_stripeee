from pathlib import Path
from pydantic_settings import BaseSettings


_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    mongo_uri: str = ""
    mongo_db: str = "stripe_demo"

    class Config:
        env_file = str(_ENV_FILE)
        env_file_encoding = "utf-8"


settings = Settings()
