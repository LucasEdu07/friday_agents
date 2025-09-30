from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

# Atalhos de tipos bem-aceitos pelo mypy + Pydantic v2
StrNonEmpty = Annotated[str, Field(min_length=1)]
IntGE0 = Annotated[int, Field(ge=0)]
IntGE1 = Annotated[int, Field(ge=1)]


class TenantFeatures(BaseModel):
    enable_text: bool = True
    enable_vision: bool = True
    enable_ocr: bool = False


class TenantLimits(BaseModel):
    # Exemplos de limites – ajuste se precisar
    max_input_tokens: IntGE1 = 4096
    max_output_tokens: IntGE1 = 1024
    max_images_per_request: IntGE0 = 4


class TenantModels(BaseModel):
    text_model: StrNonEmpty = "gpt-4o-mini"
    vision_model: StrNonEmpty = "gpt-4o"
    ocr_model: StrNonEmpty = "tesseract"


class TenantCORS(BaseModel):
    origins: list[StrNonEmpty] = Field(default_factory=list)


class TenantConfig(BaseModel):
    # nome do tenant (exibido no /v1/ping)
    name: StrNonEmpty

    features: TenantFeatures
    limits: TenantLimits
    models: TenantModels
    cors: TenantCORS
