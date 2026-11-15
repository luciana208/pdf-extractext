from pydantic import BaseModel, Field


class ReservationRequestDTO(BaseModel):
    saga_id: str = Field(min_length=1, max_length=64, description="Id de la saga que reserva.")
    checksum: str = Field(pattern=r"^[a-f0-9]{64}$", description="SHA-256 del PDF.")
    filename: str = Field(min_length=1, max_length=255, description="Nombre del documento.")

    model_config = {"frozen": True}
