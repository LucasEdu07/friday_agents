from typing import Annotated

from pydantic import Field, StringConstraints

from services.shared.models import AppBaseModel  # Base com extra="forbid"

# text: strip_whitespace + min_length via StringConstraints (Pydantic v2)
TextField = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AnalyzeRequest(AppBaseModel):
    text: TextField = Field(
        ...,
        examples=["Sextinha é braba demais!"],
    )


class AnalyzeResponse(AppBaseModel):
    length: int
    word_count: int
    preview: str
