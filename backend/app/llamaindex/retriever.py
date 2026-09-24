from typing import Any

from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters

from app.llamaindex.config import get_llamaindex_settings


def retrieve(
    index: VectorStoreIndex,
    query: str,
    *,
    top_k: int | None = None,
    metadata_filters: dict[str, str | int | float] | None = None,
) -> list[Any]:
    """Retrieve the most relevant nodes while applying exact metadata filters."""
    settings = get_llamaindex_settings()
    limit = top_k or settings.retrieval_top_k
    if limit <= 0:
        raise ValueError("top_k must be greater than zero")

    filters = None
    if metadata_filters:
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key=key, value=value) for key, value in metadata_filters.items()]
        )
    retriever = index.as_retriever(similarity_top_k=limit, filters=filters)
    return retriever.retrieve(query)