from typing import Any

from llama_index.core.base.embeddings.base import BaseEmbedding

from app.llamaindex.config import get_llamaindex_settings


def create_bge_m3_embedding(**kwargs: Any) -> BaseEmbedding:
    """Create the optional BGE-M3 adapter when its integration is installed."""
    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    except ImportError as exc:
        raise RuntimeError(
            "BGE-M3 is not installed. Install llama-index-embeddings-huggingface "
            "and sentence-transformers before enabling it."
        ) from exc

    settings = get_llamaindex_settings()
    return HuggingFaceEmbedding(
        model_name=settings.bge_m3_model_name,
        **kwargs,
    )