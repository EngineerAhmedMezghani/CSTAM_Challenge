import json

import pytest

from app.core.config import settings
from app.llm_extractor import groq_extractor


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [type("Choice", (), {"message": FakeMessage(content)})()]


class FakeCompletions:
    def __init__(self, content: str) -> None:
        self.content = content
        self.called = False

    def create(self, **kwargs):
        self.called = True
        assert kwargs["response_format"]["type"] == "json_schema"
        assert kwargs["response_format"]["json_schema"]["strict"] is True
        return FakeResponse(self.content)


class FakeClient:
    def __init__(self, content: str) -> None:
        self.chat = type("Chat", (), {"completions": FakeCompletions(content)})()


def test_extract_tender_returns_validated_structured_data(monkeypatch):
    payload = {
        "type": "rfp",
        "title": "Cloud migration services",
        "description": "Migration of internal services to a public cloud.",
        "reference": "RFP-2026-04",
        "organization": "Example Agency",
        "publication_date": "2026-09-01",
        "deadline": "2026-10-15 17:00 CET",
        "location": None,
        "category": "IT services",
        "required_skills": ["Kubernetes"],
        "required_experience": None,
        "budget": None,
        "eligibility_requirements": [],
        "technical_requirements": ["The platform must support SSO."],
        "documents_required": ["Technical proposal"],
        "source_url": "https://example.test/rfp-2026-04",
    }
    fake_client = FakeClient(json.dumps(payload))
    monkeypatch.setattr(groq_extractor, "_client", lambda: fake_client)

    result = groq_extractor.extract_tender(
        "RFP-2026-04: Cloud migration services. Deadline: 2026-10-15 17:00 CET.",
        source_url="https://example.test/rfp-2026-04",
    )

    assert result["type"] == "rfp"
    assert result["required_skills"] == ["Kubernetes"]
    assert result["budget"] is None
    assert fake_client.chat.completions.called


def test_extract_tender_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", None)

    with pytest.raises(groq_extractor.GroqExtractionError, match="GROQ_API_KEY"):
        groq_extractor.extract_tender("A tender with a deadline on 2026-10-15.")