import base64
import binascii

from pydantic import Field, field_validator

from services.shared.models import AppBaseModel


class VisionAnalyzeRequest(AppBaseModel):
    image_base64: str = Field(..., min_length=1, description="Imagem codificada em base64")

    @field_validator("image_base64")
    @classmethod
    def validate_b64(cls, v: str) -> str:
        try:
            base64.b64decode(v, validate=True)
        except (binascii.Error, ValueError) as e:
            raise ValueError("image_base64 inválido") from e
        return v


class VisionAnalyzeResponse(AppBaseModel):
    size_bytes: int
    format: str  # png | jpeg | unknown
