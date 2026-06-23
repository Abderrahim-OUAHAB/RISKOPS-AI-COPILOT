from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI RiskOps Copilot"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://riskops:riskops@postgres:5432/riskops"
    raw_data_dir: str = "data/raw"
    openai_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
