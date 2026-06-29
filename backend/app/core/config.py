from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI RiskOps Copilot"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://riskops:riskops@postgres:5432/riskops"
    raw_data_dir: str = "data/raw"
    backend_cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"
    max_upload_size_mb: int = 10
    rate_limit_per_minute: int = 60
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"
    embedding_dimensions: int = 1536
    chunk_size: int = 800
    chunk_overlap: int = 120
    rag_top_k: int = 4
    rag_similarity_threshold: float = 0.30
    churn_model_path: str = "ml/models/churn_model.pkl"
    churn_features_path: str = "ml/models/churn_features.json"
    mlflow_tracking_uri: str = "file:./mlruns"
    mlflow_experiment_name: str = "riskops-churn-model"
    log_level: str = "INFO"
    enable_langfuse: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    llm_traces_path: str = "monitoring/logs/llm_traces.jsonl"
    ml_monitoring_report_path: str = "monitoring/reports/ml_data_quality_report.html"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        raw_origins = self.backend_cors_origins.strip()
        if raw_origins.startswith("[") and raw_origins.endswith("]"):
            raw_origins = raw_origins[1:-1]
        return [
            origin.strip().strip('"').strip("'")
            for origin in raw_origins.split(",")
            if origin.strip()
        ]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


settings = Settings()
