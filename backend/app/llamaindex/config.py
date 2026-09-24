from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LlamaIndexSettings(BaseSettings):
    chunk_size: int = Field(default=1024, gt=0)
    chunk_overlap: int = Field(default=200, ge=0)
    retrieval_top_k: int = Field(default=5, gt=0)
    bge_m3_model_name: str = "BAAI/bge-m3"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_prefix="LLAMAINDEX_",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_llamaindex_settings() -> LlamaIndexSettings:
    return LlamaIndexSettings()