from pydantic_settings import BaseSettings
from pydantic import Field

class ScoringSettings(BaseSettings):
    weight_domain_age: float = Field(default=12.0)
    weight_ssl_certificate: float = Field(default=10.0)
    weight_policy_pages_presence: float = Field(default=15.0)
    weight_red_flags: float = Field(default=20.0)
    weight_github_public_footprint: float = Field(default=10.0)
    weight_linkedin_public_footprint: float = Field(default=10.0)
    weight_product_claims_quality: float = Field(default=23.0)

    class Config:
        env_file = ".env"
        extra = "ignore"

scoring_settings = ScoringSettings()