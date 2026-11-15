from pydantic import BaseModel, Field


class ConfirmRequestDTO(BaseModel):
    saga_id: str = Field(min_length=1, max_length=64, description="Id de la saga duena de la reserva.")
    extracted_text: str = Field(description="Texto extraido del PDF.")

    model_config = {"frozen": True}
