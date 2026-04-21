from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AI Due Diligence"
    database_url: str = "sqlite:///./ai_due_diligence.db"
    api_key: str = "super-secret-key"  # ou laissez vide

    # scoring weights
    w_vulnerabilities: float = 0.1
    w_config: float = 0.3
    w_reputation: float = 0.6

    # thresholds (directement définis)
    threshold_high: float = 0.7
    threshold_medium: float = 0.4

    ml_model_path: str = "artifacts/risk_model.joblib"

settings = Settings()




















# from pydantic_settings import BaseSettings, SettingsConfigDict




# class Settings(BaseSettings):
#     app_name: str = "AI Due Diligence"
#     database_url: str = "sqlite:///./ai_due_diligence.db"
#     api_key: str = ""

#     # scoring weights
#     w_vulnerabilities: float = 0.40
#     w_config: float = 0.30
#     w_reputation: float = 0.30

#     # thresholds
#     threshold_high: float = 0.70
#     threshold_medium: float = 0.40

#     model_config = SettingsConfigDict(env_file=".env", extra="ignore")

#     ml_model_path: str = "artifacts/risk_model.joblib"

    
# settings = Settings()