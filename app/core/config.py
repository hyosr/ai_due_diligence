from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AI Due Diligence"
    database_url: str = "sqlite:///./ai_due_diligence.db"
    api_key: str = ""

settings = Settings()



