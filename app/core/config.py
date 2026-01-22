from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NOIRID"
    env: str = "dev"
    secret_key: str = "secret"

    database_url: str
    session_cookie_name: str = "noirid_session"

    tco_merchant_code: str
    tco_secret_word: str
    tco_secret_key: str
    tco_demo: str = "1"

settings = Settings()