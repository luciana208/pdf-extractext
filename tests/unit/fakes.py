"""repositorio en memoria que respeta el contrato de IDocumentRepository"""

from dataclasses import replace
from datetime import datetime, timezone
from itertools import count

from app.business.domain.exceptions import DuplicateDocumentError
from app.business.entities.document import Document, DocumentStatus
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository

CHECKSUM = "a" * 64
OTHER_CHECKSUM = "b" * 64


class InMemoryDocumentRepository(IDocumentRepository):
    def __init__(self) -> None:
        self.documents: dict[str, Document] = {}
        self._ids = count(1)

    async def save(self, document: Document) -> Document:
        if any(existing.checksum == document.checksum for existing in self.documents.values()):
            raise DuplicateDocumentError(document.checksum)
        saved = replace(document, id=f"{next(self._ids):024x}")
        self.documents[saved.id] = saved
        return saved

    async def get_by_checksum(self, checksum: str) -> Document | None:
        return next((d for d in self.documents.values() if d.checksum == checksum), None)

    async def complete(self, document_id: str, saga_id: str, extracted_text: str) -> Document | None:
        document = self.documents.get(document_id)
        if document is None or not document.is_pending() or not document.belongs_to(saga_id):
            return None
        completed = replace(
            document,
            status=DocumentStatus.COMPLETED,
            extracted_text=extracted_text,
            expires_at=None,
            updated_at=datetime.now(timezone.utc),
        )
        self.documents[document_id] = completed
        return completed

    async def delete_reservation(self, document_id: str, saga_id: str) -> bool:
        document = self.documents.get(document_id)
        if document is None or not document.is_pending() or not document.belongs_to(saga_id):
            return False
        del self.documents[document_id]
        return True

    def _completed(self) -> list[Document]:
        return [d for d in self.documents.values() if not d.is_pending()]

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Document]:
        return self._completed()[skip : skip + limit]

    async def get_by_id(self, document_id: str) -> Document | None:
        document = self.documents.get(document_id)
        return document if document and not document.is_pending() else None

    async def update(self, document_id: str, fields: dict) -> Document | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None
        changes = {"filename": fields["filename"]} if "filename" in fields else {}
        updated = replace(document, **changes, updated_at=datetime.now(timezone.utc))
        self.documents[document_id] = updated
        return updated

    async def delete(self, document_id: str) -> bool:
        if await self.get_by_id(document_id) is None:
            return False
        del self.documents[document_id]
        return True
