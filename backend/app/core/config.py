from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "MedIntel Clinical Workflow AI Agent"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    token_exp_minutes: int = 120
    llm_provider: str = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    allowed_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()
