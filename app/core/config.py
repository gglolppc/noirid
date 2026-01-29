from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NOIRID"
    env: str = "dev"
    secret_key: str = "secret"
    MAILGUN_API_KEY: str

    database_url: str
    session_cookie_name: str = "noirid_session"

    tco_merchant_code: str
    tco_secret_word: str
    tco_secret_key: str
    tco_demo: str = "1"
    standard_shipping_fee_usd: str = "4.99"

settings = Settings()
