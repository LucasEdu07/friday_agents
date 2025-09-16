from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field (..., min_lenght=1, description="Texto para análise")

class AnalyzeResponse(BaseModel):
    length: int
    word_count: int
    preview: str