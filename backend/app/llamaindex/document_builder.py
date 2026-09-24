import json
from collections.abc import Iterable
from typing import Any

from llama_index.core import Document

_COMMON_METADATA = (
    "organization",
    "category",
    "location",
    "deadline",
    "publication_date",
    "source_url",
    "reference",
    "year",
    "region",
)

_TEXT_FIELDS = {
    "rfp": (
        "title",
        "description",
        "category",
        "required_skills",
        "required_experience",
        "eligibility_requirements",
        "technical_requirements",
        "documents_required",
    ),
    "cv": (
        "name",
        "summary",
        "profile",
        "skills",
        "experience",
        "projects",
        "education",
        "certifications",
    ),
    "olivesoft": (
        "variety",
        "region",
        "year",
        "yield",
        "soil",
        "description",
    ),
}

_TYPE_METADATA_FIELDS = {
    "cv": ("name",),
    "olivesoft": ("variety", "soil", "yield"),
}


def _display_value(value: Any) -> str:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _metadata_value(value: Any) -> str | int | float:
    if isinstance(value, (str, int, float)):
        return value
    return _display_value(value)


def _format_text_field(field_name: str, value: Any) -> str:
    label = field_name.replace("_", " ").title()
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        content = ", ".join(value)
    else:
        content = _display_value(value)
    return f"{label}:\n{content}"


def build_document(data: dict[str, Any], data_type: str) -> Document:
    """Convert one structured record into semantic text plus filterable metadata."""
    normalized_type = data_type.strip().lower()
    if not normalized_type:
        raise ValueError("data_type must not be empty")
    if not isinstance(data, dict):
        raise TypeError("data must be a dictionary")

    metadata: dict[str, str | int | float] = {"data_type": normalized_type}
    for key in _COMMON_METADATA:
        value = data.get(key)
        if value is not None and value != "":
            metadata[key] = _metadata_value(value)
    for key in _TYPE_METADATA_FIELDS.get(normalized_type, ()):
        value = data.get(key)
        if value is not None and value != "":
            metadata[key] = _metadata_value(value)

    text_fields = _TEXT_FIELDS.get(normalized_type)
    if text_fields is None:
        text_fields = tuple(key for key in data if key not in _COMMON_METADATA and key != "type")

    sections = [
        _format_text_field(key, data[key])
        for key in text_fields
        if data.get(key) is not None and data.get(key) != ""
    ]
    if not sections:
        raise ValueError("data must contain at least one semantic field")

    metadata_keys = list(metadata)
    return Document(
        text="\n\n".join(sections),
        metadata=metadata,
        excluded_embed_metadata_keys=metadata_keys,
        excluded_llm_metadata_keys=metadata_keys,
    )


def build_documents(records: Iterable[dict[str, Any]], data_type: str) -> list[Document]:
    return [build_document(record, data_type) for record in records]