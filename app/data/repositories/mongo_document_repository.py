"""implementacion de IDocumentRepository sobre mongodb (beanie)"""

import logging
from datetime import datetime, timezone

from beanie import PydanticObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.business.domain.exceptions import DuplicateDocumentError
from app.business.entities.document import Document, DocumentStatus
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository
from app.data.models.document_model import DocumentModel

logger = logging.getLogger(__name__)

COMPLETED = DocumentStatus.COMPLETED.value
PENDING = DocumentStatus.PENDING.value


def _object_id(document_id: str) -> PydanticObjectId | None:
    # un id con formato invalido no puede existir
    try:
        return PydanticObjectId(document_id)
    except (InvalidId, TypeError):
        return None


class MongoDocumentRepository(IDocumentRepository):

    async def save(self, document: Document) -> Document:
        model = DocumentModel.from_entity(document)
        try:
            await model.insert()
        except DuplicateKeyError:
            logger.warning("documento duplicado checksum=%s", document.checksum)
            raise DuplicateDocumentError(document.checksum)
        return model.to_entity()

    async def get_by_checksum(self, checksum: str) -> Document | None:
        model = await DocumentModel.find_one(DocumentModel.checksum == checksum)
        return model.to_entity() if model else None

    async def complete(self, document_id: str, saga_id: str, extracted_text: str) -> Document | None:
        object_id = _object_id(document_id)
        if object_id is None:
            return None
        # update atomico: solo pasa si sigue pendiente y es de esta saga
        model = await DocumentModel.get_pymongo_collection().find_one_and_update(
            {"_id": object_id, "saga_id": saga_id, "status": PENDING},
            {
                "$set": {
                    "status": COMPLETED,
                    "extracted_text": extracted_text,
                    "expires_at": None,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        return DocumentModel.model_validate(model).to_entity() if model else None

    async def delete_reservation(self, document_id: str, saga_id: str) -> bool:
        object_id = _object_id(document_id)
        if object_id is None:
            return False
        result = await DocumentModel.get_pymongo_collection().delete_one(
            {"_id": object_id, "saga_id": saga_id, "status": PENDING}
        )
        return result.deleted_count == 1

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Document]:
        models = (
            await DocumentModel.find(DocumentModel.status == COMPLETED)
            .sort(+DocumentModel.created_at)
            .skip(skip)
            .limit(limit)
            .to_list()
        )
        return [model.to_entity() for model in models]

    async def get_by_id(self, document_id: str) -> Document | None:
        model = await self._find_completed(document_id)
        return model.to_entity() if model else None

    async def update(self, document_id: str, fields: dict) -> Document | None:
        model = await self._find_completed(document_id)
        if model is None:
            return None
        # solo los metadatos se pueden modificar
        changes: dict = {DocumentModel.updated_at: datetime.now(timezone.utc)}
        if "filename" in fields:
            changes[DocumentModel.name] = fields["filename"]
        await model.set(changes)
        logger.info("documento actualizado id=%s", document_id)
        return model.to_entity()

    async def delete(self, document_id: str) -> bool:
        model = await self._find_completed(document_id)
        if model is None:
            return False
        await model.delete()
        logger.info("documento eliminado id=%s", document_id)
        return True

    @staticmethod
    async def _find_completed(document_id: str) -> DocumentModel | None:
        object_id = _object_id(document_id)
        if object_id is None:
            return None
        return await DocumentModel.find_one(DocumentModel.id == object_id, DocumentModel.status == COMPLETED)
