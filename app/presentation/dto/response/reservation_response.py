from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from app.business.entities.document import Document


class ReservationResponseDTO(BaseModel):
    id: str = Field(description="Id del documento reservado.")
    status: str = Field(description="Estado de la reserva (pending).")
    expires_at: datetime = Field(description="Momento en que la reserva vence si no se confirma.")

    model_config = {"frozen": True}

    @field_serializer("expires_at")
    def _serialize_date(self, moment: datetime) -> str:
        return moment.isoformat()

    @classmethod
    def from_entity(cls, document: Document) -> "ReservationResponseDTO":
        return cls(id=document.id, status=document.status.value, expires_at=document.expires_at)
