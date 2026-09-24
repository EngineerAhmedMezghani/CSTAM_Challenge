from typing import Any

from llama_index.core.base.embeddings.base import BaseEmbedding

from app.llamaindex.document_builder import build_document
from app.llamaindex.indexer import chunk_documents, create_index
from app.llamaindex.retriever import retrieve


class KeywordEmbedding(BaseEmbedding):
    """Small deterministic test embedding; production will use BGE-M3."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(model_name="test-keyword", **kwargs)

    @staticmethod
    def _vector(text: str) -> list[float]:
        terms = ("python", "fastapi", "postgresql", "olive", "kubernetes")
        lowered = text.lower()
        return [float(lowered.count(term)) for term in terms]

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._vector(text)

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._vector(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)


def test_rfp_json_becomes_document_with_separated_metadata():
    document = build_document(
        {
            "type": "rfp",
            "title": "Development of a Web Platform",
            "description": "Build a public web platform.",
            "organization": "Company X",
            "category": "Software Development",
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
            "location": "Tunisia",
            "deadline": "2026-10-15",
            "source_url": "https://example.test/rfp",
            "reference": "RFP-42",
        },
        "rfp",
    )

    assert "Development of a Web Platform" in document.text
    assert "Python, FastAPI, PostgreSQL" in document.text
    assert document.metadata["data_type"] == "rfp"
    assert document.metadata["deadline"] == "2026-10-15"
    assert document.metadata["source_url"] == "https://example.test/rfp"
    assert document.metadata["reference"] == "RFP-42"
    assert set(document.excluded_embed_metadata_keys) == set(document.metadata)


def test_cv_and_olivesoft_documents_are_type_specific():
    cv = build_document(
        {"name": "Amina", "skills": ["Python"], "experience": ["Backend engineer"]},
        "cv",
    )
    olivesoft = build_document(
        {"variety": "Chemlali", "region": "Sfax", "year": 2025, "yield": 3200, "soil": "Clay"},
        "olivesoft",
    )

    assert "Backend engineer" in cv.text
    assert cv.metadata == {"data_type": "cv", "name": "Amina"}
    assert "Chemlali" in olivesoft.text
    assert olivesoft.metadata["data_type"] == "olivesoft"
    assert olivesoft.metadata["year"] == 2025
    assert olivesoft.metadata["yield"] == 3200


def test_long_text_is_chunked_and_metadata_is_preserved():
    document = build_document(
        {
            "title": "Long RFP",
            "description": "Technical requirement " * 120,
            "source_url": "https://example.test/long-rfp",
            "reference": "LONG-1",
        },
        "rfp",
    )

    nodes = chunk_documents([document], chunk_size=80, chunk_overlap=10)

    assert len(nodes) > 1
    assert all(node.metadata["source_url"] == "https://example.test/long-rfp" for node in nodes)
    assert all(node.metadata["reference"] == "LONG-1" for node in nodes)


def test_retrieval_returns_results_and_applies_data_type_filter():
    documents = [
        build_document(
            {"title": "Python FastAPI CV", "skills": ["Python", "FastAPI"], "name": "Amina"},
            "cv",
        ),
        build_document(
            {"title": "Olive cultivation report", "description": "Olive production in Sfax."},
            "olivesoft",
        ),
    ]
    index = create_index(documents, embed_model=KeywordEmbedding(), chunk_size=256, chunk_overlap=20)

    results = retrieve(index, "Python FastAPI developer", metadata_filters={"data_type": "cv"})

    assert results
    assert all(result.node.metadata["data_type"] == "cv" for result in results)
    assert results[0].node.metadata["name"] == "Amina"