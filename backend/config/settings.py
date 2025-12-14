"""Application configuration settings."""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "RFP Response System"
    environment: str = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Database
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # AI Models
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_llm_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    
    # Agents
    technical_agent_model: str = "gpt-4-turbo-preview"
    pricing_agent_model: str = "gpt-4-turbo-preview"
    parallel_execution: bool = True
    max_agent_retries: int = 3
    
    # Vector Database
    chroma_persist_dir: str = "./data/chromadb"
    
    # Data Paths
    data_dir: Path = Path("../FMEG_data")
    wires_cables_dir: Path = Path("../wires_cables_data")
    standards_dir: Path = Path("../wires_cables_standards")
    testing_data_dir: Path = Path("../testing_data")
    rfp_input_dir: Path = Path("../RFPs")
    output_dir: Path = Path("./outputs")
    
    # Security
    secret_key: str
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
