from collections.abc import Sequence
from typing import Any

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode

from app.llamaindex.config import get_llamaindex_settings


def chunk_documents(
    documents: Sequence[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[BaseNode]:
    """Split semantic text while carrying document metadata onto every node."""
    settings = get_llamaindex_settings()
    size = chunk_size or settings.chunk_size
    overlap = settings.chunk_overlap if chunk_overlap is None else chunk_overlap
    if overlap >= size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    parser = SentenceSplitter(chunk_size=size, chunk_overlap=overlap)
    return parser.get_nodes_from_documents(list(documents))


def create_index(
    documents: Sequence[Document],
    embed_model: BaseEmbedding | str | None = None,
    *,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    **index_kwargs: Any,
) -> VectorStoreIndex:
    """Create an in-memory index; pass storage_context later for Qdrant."""
    if embed_model is None:
        raise ValueError(
            "embed_model is required; provide the BGE-M3 adapter explicitly."
        )
    nodes = chunk_documents(documents, chunk_size, chunk_overlap)
    if not nodes:
        raise ValueError("at least one document with semantic content is required")
    return VectorStoreIndex(nodes=nodes, embed_model=embed_model, **index_kwargs)