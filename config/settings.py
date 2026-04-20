from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore",
        protected_namespaces=('settings_',)   # ← fixes the model_path warning
    )

    app_name: str = "FinanceAI"
    app_env: str = "development"
    secret_key: str = "change-me"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./financeai.db"
    model_path: str = "data/classifier.joblib"

    confidence_auto: float = 0.85
    confidence_show: float = 0.65
    confidence_suggest: float = 0.45

    split_window_days: int = 7
    split_min_amount: float = 10.0
    review_auto_assign_days: int = 7

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()