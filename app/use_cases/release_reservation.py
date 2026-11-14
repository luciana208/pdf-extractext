import logging

from app.business.repositories.interfaces.i_document_repository import IDocumentRepository

logger = logging.getLogger(__name__)


class ReleaseReservationUseCase:
    """compensacion de la saga: borra la reserva; es idempotente, si no existe no hace nada"""

    def __init__(self, repository: IDocumentRepository) -> None:
        self._repository = repository

    async def execute(self, document_id: str, saga_id: str) -> None:
        released = await self._repository.delete_reservation(document_id, saga_id)
        logger.info("compensacion id=%s saga=%s liberada=%s", document_id, saga_id, released)
