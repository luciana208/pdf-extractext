from datetime import datetime, timedelta, timezone

import pytest

from app.business.domain.exceptions import DuplicateDocumentError, ReservationNotFoundError
from app.business.entities.document import DocumentStatus
from app.use_cases.confirm_document import ConfirmDocumentUseCase
from app.use_cases.release_reservation import ReleaseReservationUseCase
from app.use_cases.reserve_document import ReserveDocumentUseCase
from tests.unit.fakes import CHECKSUM, InMemoryDocumentRepository

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def repo():
    return InMemoryDocumentRepository()


def reserve_use_case(repo, now=NOW):
    return ReserveDocumentUseCase(repo, ttl_seconds=300, clock=lambda: now)


async def test_reserva_crea_documento_pendiente_con_vencimiento(repo):
    reservation = await reserve_use_case(repo).execute("s1", CHECKSUM, "a.pdf")
    assert reservation.is_persisted()
    assert reservation.status == DocumentStatus.PENDING
    assert reservation.saga_id == "s1"
    assert reservation.expires_at == NOW + timedelta(seconds=300)


async def test_reserva_de_checksum_completado_es_duplicado(repo):
    reservation = await reserve_use_case(repo).execute("s1", CHECKSUM, "a.pdf")
    await ConfirmDocumentUseCase(repo).execute(reservation.id, "s1", "texto")
    with pytest.raises(DuplicateDocumentError):
        await reserve_use_case(repo).execute("s2", CHECKSUM, "b.pdf")


async def test_reserva_vigente_de_otra_saga_es_duplicado(repo):
    await reserve_use_case(repo).execute("s1", CHECKSUM, "a.pdf")
    with pytest.raises(DuplicateDocumentError):
        await reserve_use_case(repo).execute("s2", CHECKSUM, "a.pdf")


async def test_reintento_de_la_misma_saga_devuelve_la_misma_reserva(repo):
    first = await reserve_use_case(repo).execute("s1", CHECKSUM, "a.pdf")
    second = await reserve_use_case(repo).execute("s1", CHECKSUM, "a.pdf")
    assert first.id == second.id
    assert len(repo.documents) == 1


async def test_reserva_vencida_se_reemplaza(repo):
    old = await reserve_use_case(repo).execute("s1", CHECKSUM, "a.pdf")
    later = NOW + timedelta(seconds=301)
    new = await reserve_use_case(repo, now=later).execute("s2", CHECKSUM, "a.pdf")
    assert new.id != old.id
    assert new.saga_id == "s2"
    assert len(repo.documents) == 1


async def test_confirmar_completa_el_documento_con_el_texto(repo):
    reservation = await reserve_use_case(repo).execute("s1", CHECKSUM, "a.pdf")
    document = await ConfirmDocumentUseCase(repo).execute(reservation.id, "s1", "texto extraido")
    assert document.status == DocumentStatus.COMPLETED
    assert document.extracted_text == "texto extraido"
    assert document.expires_at is None


async def test_confirmar_dos_veces_es_idempotente(repo):
    reservation = await reserve_use_case(repo).execute("s1", CHECKSUM, "a.pdf")
    first = await ConfirmDocumentUseCase(repo).execute(reservation.id, "s1", "texto")
    second = await ConfirmDocumentUseCase(repo).execute(reservation.id, "s1", "texto")
    assert first.id == second.id


async def test_confirmar_con_otra_saga_falla(repo):
    reservation = await reserve_use_case(repo).execute("s1", CHECKSUM, "a.pdf")
    with pytest.raises(ReservationNotFoundError):
        await ConfirmDocumentUseCase(repo).execute(reservation.id, "otra", "texto")


async def test_confirmar_reserva_inexistente_falla(repo):
    with pytest.raises(ReservationNotFoundError):
        await ConfirmDocumentUseCase(repo).execute("no-existe", "s1", "texto")


async def test_liberar_borra_la_reserva(repo):
    reservation = await reserve_use_case(repo).execute("s1", CHECKSUM, "a.pdf")
    await ReleaseReservationUseCase(repo).execute(reservation.id, "s1")
    assert repo.documents == {}


async def test_liberar_es_idempotente(repo):
    await ReleaseReservationUseCase(repo).execute("no-existe", "s1")


async def test_liberar_no_borra_un_documento_completado(repo):
    reservation = await reserve_use_case(repo).execute("s1", CHECKSUM, "a.pdf")
    await ConfirmDocumentUseCase(repo).execute(reservation.id, "s1", "texto")
    await ReleaseReservationUseCase(repo).execute(reservation.id, "s1")
    assert len(repo.documents) == 1
