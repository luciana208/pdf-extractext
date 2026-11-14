"""entidad de dominio document: un pdf procesado o reservado por una saga"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"


@dataclass
class Document:
    """
    checksum y extracted_text no cambian una vez completado; solo filename se puede editar.
    un documento pending es una reserva de la saga y vence en expires_at.
    """

    filename: str
    checksum: str
    extracted_text: str = ""
    status: DocumentStatus = DocumentStatus.COMPLETED
    saga_id: str | None = None
    expires_at: datetime | None = None

    id: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def is_persisted(self) -> bool:
        return self.id is not None

    def is_pending(self) -> bool:
        return self.status == DocumentStatus.PENDING

    def is_expired_reservation(self, now: datetime) -> bool:
        return self.is_pending() and self.expires_at is not None and self.expires_at <= now

    def belongs_to(self, saga_id: str) -> bool:
        return self.saga_id == saga_id
