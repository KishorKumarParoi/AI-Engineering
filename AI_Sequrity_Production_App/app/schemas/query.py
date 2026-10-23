"""Strict Pydantic V2 models for API request/response validation."""

from pydantic import BaseModel, Field, field_validator
import re


class QueryRequest(BaseModel):
    q: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User query string for guardrail verification and RAG processing",
    )
    thread_id: str = Field(
        default="default_user",
        min_length=1,
        max_length=128,
        description="Session conversation thread identifier",
    )

    @field_validator("q")
    @classmethod
    def sanitize_whitespace(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", " ", v).strip()
        if not cleaned:
            raise ValueError("Query cannot be empty or pure whitespace.")
        return cleaned


class QueryResponse(BaseModel):
    question: str
    answer: str
    thought_process: list[str] = Field(default_factory=list)
    status: str
    sources: list[str] = Field(default_factory=list)
