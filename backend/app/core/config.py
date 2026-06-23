from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI RiskOps Copilot"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://riskops:riskops@postgres:5432/riskops"
    raw_data_dir: str = "data/raw"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"
    embedding_dimensions: int = 1536
    chunk_size: int = 800
    chunk_overlap: int = 120
    rag_top_k: int = 4
    rag_similarity_threshold: float = 0.55

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
