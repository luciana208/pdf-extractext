"""modelo de persistencia en mongodb (beanie), solo vive en la capa de datos"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from beanie import Document
from pydantic import Field
from pymongo import IndexModel

if TYPE_CHECKING:
    from app.business.entities.document import Document as DocumentEntity


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentModel(Document):
    """
    coleccion documents. el indice unico de checksum frena duplicados aun con uploads simultaneos;
    el indice ttl sobre expires_at borra solo las reservas vencidas (los completados lo tienen en null).
    """

    name: str
    checksum: str
    extracted_text: str = ""
    status: str = "completed"
    saga_id: str | None = None
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    class Settings:
        name = "documents"
        indexes = [
            IndexModel([("checksum", 1)], unique=True, name="checksum_unique"),
            IndexModel([("expires_at", 1)], expireAfterSeconds=0, name="reservation_ttl"),
            IndexModel([("status", 1), ("created_at", 1)], name="status_created_at"),
        ]

    def to_entity(self) -> "DocumentEntity":
        from app.business.entities.document import Document as DocumentEntity, DocumentStatus

        return DocumentEntity(
            id=str(self.id) if self.id else None,
            filename=self.name,
            checksum=self.checksum,
            extracted_text=self.extracted_text,
            status=DocumentStatus(self.status),
            saga_id=self.saga_id,
            expires_at=_as_utc(self.expires_at),
            created_at=_as_utc(self.created_at),
            updated_at=_as_utc(self.updated_at),
        )

    @classmethod
    def from_entity(cls, entity: "DocumentEntity") -> "DocumentModel":
        return cls(
            name=entity.filename,
            checksum=entity.checksum,
            extracted_text=entity.extracted_text,
            status=entity.status.value,
            saga_id=entity.saga_id,
            expires_at=entity.expires_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


def _as_utc(moment: datetime | None) -> datetime | None:
    # mongo guarda en utc pero puede devolver fechas sin zona horaria
    if moment is None:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
