import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from app.business.domain.exceptions import DuplicateDocumentError
from app.business.entities.document import Document, DocumentStatus, utc_now
from app.business.repositories.interfaces.i_document_repository import IDocumentRepository

logger = logging.getLogger(__name__)


class ReserveDocumentUseCase:
    """
    paso de la saga que aparta el checksum antes de extraer.
    si el checksum ya existe es duplicado, salvo que sea una reserva vencida o un reintento de la misma saga.
    """

    def __init__(
        self, repository: IDocumentRepository, ttl_seconds: int, clock: Callable[[], datetime] = utc_now
    ) -> None:
        self._repository = repository
        self._ttl = timedelta(seconds=ttl_seconds)
        self._clock = clock

    async def execute(self, saga_id: str, checksum: str, filename: str) -> Document:
        now = self._clock()
        existing = await self._repository.get_by_checksum(checksum)
        if existing is not None:
            if existing.is_pending() and existing.belongs_to(saga_id):
                return existing
            if not existing.is_expired_reservation(now):
                raise DuplicateDocumentError(checksum)
            # reserva vencida que el ttl de mongo todavia no limpio
            logger.info("se libera reserva vencida id=%s", existing.id)
            await self._repository.delete_reservation(existing.id, existing.saga_id)

        reservation = Document(
            filename=filename,
            checksum=checksum,
            status=DocumentStatus.PENDING,
            saga_id=saga_id,
            expires_at=now + self._ttl,
            created_at=now,
            updated_at=now,
        )
        saved = await self._repository.save(reservation)
        logger.info("reserva creada id=%s saga=%s", saved.id, saga_id)
        return saved
