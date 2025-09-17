from pydantic import BaseModel, Field

class VisionAnalyzeRequest(BaseModel):
    image_base64: str = Field(
        ..., min_length=1, description="Imagem codificada em base64"
    )

class VisionAnalyzeResponse(BaseModel):
    size_bytes: int
    format: str  # png | jpeg | unknown
