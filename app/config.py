"""
SRE RAG Agent — Configuration Module
Loads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = Field(default="sre-rag-api", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(
        default="development",
        description="Deployment environment: development, staging, or production",
    )
    enable_docs: bool = Field(
        default=True,
        description="Enable Swagger/OpenAPI docs (auto-disabled in production)",
    )
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format: json or console")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    workers: int = Field(default=2, description="Number of workers")

    # PostgreSQL
    postgres_host: str = Field(default="postgresql", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="sre_rag", description="PostgreSQL database")
    postgres_user: str = Field(default="sre_user", description="PostgreSQL user")
    postgres_password: str = Field(
        default="",
        description="PostgreSQL password — MUST be set via POSTGRES_PASSWORD env var in production",
    )

    # Redis
    redis_host: str = Field(default="redis", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: str = Field(default="", description="Redis password")

    # RAG
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings",
    )
    chunk_size: int = Field(default=512, description="Document chunk size")
    chunk_overlap: int = Field(default=50, description="Chunk overlap size")
    top_k: int = Field(default=5, description="Number of top results to retrieve")

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def docs_url(self) -> str | None:
        if self.is_production or not self.enable_docs:
            return None
        return "/docs"

    @property
    def openapi_url(self) -> str | None:
        if self.is_production or not self.enable_docs:
            return None
        return "/openapi.json"

    @property
    def redoc_url(self) -> str | None:
        if self.is_production or not self.enable_docs:
            return None
        return "/redoc"

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()
