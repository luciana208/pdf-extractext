import logging

from app.business.domain.exceptions import ReservationNotFoundError
from app.business.entities.document import Document
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository

logger = logging.getLogger(__name__)


class ConfirmDocumentUseCase:
    """ultimo paso de la saga: guarda el texto y deja el documento completado"""

    def __init__(self, repository: IDocumentRepository) -> None:
        self._repository = repository

    async def execute(self, document_id: str, saga_id: str, extracted_text: str) -> Document:
        completed = await self._repository.complete(document_id, saga_id, extracted_text)
        if completed is not None:
            logger.info("documento confirmado id=%s saga=%s", document_id, saga_id)
            return completed

        # reintento de una confirmacion que ya se hizo: se devuelve el mismo resultado
        existing = await self._repository.get_by_id(document_id)
        if existing is not None and existing.belongs_to(saga_id):
            return existing
        raise ReservationNotFoundError(document_id)
