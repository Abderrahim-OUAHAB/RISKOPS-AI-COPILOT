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


settings = Settings()
