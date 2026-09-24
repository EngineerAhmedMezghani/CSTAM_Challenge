import json
from typing import Any, Literal

from groq import Groq
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import get_settings

MODEL = "openai/gpt-oss-120b"


class TenderExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["rfp"] = "rfp"
    title: str | None = None
    description: str | None = None
    reference: str | None = None
    organization: str | None = None
    publication_date: str | None = None
    deadline: str | None = None
    location: str | None = None
    category: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    required_experience: str | None = None
    budget: str | None = None
    eligibility_requirements: list[str] = Field(default_factory=list)
    technical_requirements: list[str] = Field(default_factory=list)
    documents_required: list[str] = Field(default_factory=list)
    source_url: str | None = None


class GroqExtractionError(RuntimeError):
    """Raised when the Groq extraction cannot produce a valid tender."""


SYSTEM_PROMPT = """You are an information extraction system for tenders and requests for proposals.
Extract only information explicitly present in the supplied source text. Never hallucinate,
infer, or invent missing facts. Use null for missing scalar fields and an empty list for
missing list fields. Preserve dates, amounts, names, and wording exactly when possible.
The description must summarize only the source text. Put concrete technologies, domains,
skills, and certifications in required_skills; technical specifications in
technical_requirements; candidate or company conditions in eligibility_requirements; and
administrative or technical submission items in documents_required. The output type is always
"rfp". Return only data matching the supplied schema."""


def _schema() -> dict[str, Any]:
    schema = TenderExtraction.model_json_schema()
    schema["required"] = list(schema["properties"])
    return schema


def _client() -> Groq:
    api_key = get_settings().groq_api_key
    if not api_key:
        raise GroqExtractionError(
            "GROQ_API_KEY environment variable is required for tender extraction."
        )
    return Groq(api_key=api_key)


def extract_tender(raw_text: str, source_url: str | None = None) -> dict[str, Any]:
    """Extract a validated tender object from raw scraper text."""
    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text must contain tender content")

    user_content = raw_text.strip()
    if source_url:
        user_content += f"\n\nSource URL: {source_url}"

    try:
        response = _client().chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "tender_extraction",
                    "strict": True,
                    "schema": _schema(),
                },
            },
            temperature=0,
        )
        content = response.choices[0].message.content
        if not content:
            raise GroqExtractionError("Groq returned an empty extraction response.")
        return TenderExtraction.model_validate(json.loads(content)).model_dump()
    except GroqExtractionError:
        raise
    except (json.JSONDecodeError, ValidationError) as exc:
        raise GroqExtractionError("Groq returned invalid tender JSON.") from exc
    except Exception as exc:
        raise GroqExtractionError("Groq tender extraction request failed.") from exc