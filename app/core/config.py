from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AI Due Diligence"
    database_url: str = "sqlite:///./ai_due_diligence.db"
    api_key: str = ""

    # IMPORTANT: permet d'avoir d'autres variables dans .env (ex: weight_*)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()