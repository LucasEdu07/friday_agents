from pydantic import Field, field_validator

from services.shared.models import AppBaseModel


class AnalyzeRequest(AppBaseModel):
    text: str = Field(..., min_length=1, description="Texto para análise")

    @field_validator("text", mode="before")
    @classmethod
    def strip_and_require(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("text must be a string")
        s = v.strip()
        if not s:
            raise ValueError("text cannot be empty or whitespace")
        return s

class AnalyzeResponse(AppBaseModel):
    length: int
    word_count: int
    preview: str
