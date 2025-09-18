from pydantic import BaseModel, ConfigDict


class AppBaseModel(BaseModel):
    """Base para todos os schemas das APIs."""

    model_config = ConfigDict(
        extra="forbid",  # rejeita campos desconhecidos
        populate_by_name=True,  # aceita alias por nome
    )
