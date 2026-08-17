from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://rag:rag@localhost:5432/rag"
    data_dir: Path = Path("./data")

    embedding_provider: str = "local"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_model_version: str = "unversioned"

    # Only read when embedding_provider == "local-lsa". The fit snapshot is part of
    # the model's identity, so query vectors and chunk vectors cannot diverge.
    lsa_fit_snapshot_id: str | None = None
    lsa_dimension: int = 384

    generation_provider: str = "openai"
    generation_model: str = "gpt-5.6"
    openai_api_key: str | None = None

    max_chunk_chars: int = 3500
    min_chunk_chars: int = 200


settings = Settings()
