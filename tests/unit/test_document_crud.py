import pytest

from app.business.domain.exceptions import DocumentNotFoundError
from app.use_cases.confirm_document import ConfirmDocumentUseCase
from app.use_cases.delete_document import DeleteDocumentUseCase
from app.use_cases.get_document import GetDocumentUseCase
from app.use_cases.list_documents import ListDocumentsUseCase
from app.use_cases.reserve_document import ReserveDocumentUseCase
from app.use_cases.update_document import UpdateDocumentUseCase
from tests.unit.fakes import CHECKSUM, OTHER_CHECKSUM, InMemoryDocumentRepository


@pytest.fixture
def repo():
    return InMemoryDocumentRepository()


async def completed(repo, checksum=CHECKSUM, saga_id="s1"):
    reservation = await ReserveDocumentUseCase(repo, 300).execute(saga_id, checksum, "a.pdf")
    return await ConfirmDocumentUseCase(repo).execute(reservation.id, saga_id, "texto")


async def test_listar_no_muestra_reservas_pendientes(repo):
    await completed(repo)
    await ReserveDocumentUseCase(repo, 300).execute("s2", OTHER_CHECKSUM, "b.pdf")
    documents = await ListDocumentsUseCase(repo).execute()
    assert [d.checksum for d in documents] == [CHECKSUM]


async def test_obtener_documento_completado(repo):
    document = await completed(repo)
    assert (await GetDocumentUseCase(repo).execute(document.id)).id == document.id


async def test_obtener_reserva_pendiente_da_not_found(repo):
    reservation = await ReserveDocumentUseCase(repo, 300).execute("s1", CHECKSUM, "a.pdf")
    with pytest.raises(DocumentNotFoundError):
        await GetDocumentUseCase(repo).execute(reservation.id)


async def test_renombrar(repo):
    document = await completed(repo)
    updated = await UpdateDocumentUseCase(repo).execute(document.id, {"filename": "nuevo.pdf"})
    assert updated.filename == "nuevo.pdf"
    assert updated.extracted_text == "texto"


async def test_renombrar_inexistente_da_not_found(repo):
    with pytest.raises(DocumentNotFoundError):
        await UpdateDocumentUseCase(repo).execute("no-existe", {"filename": "x.pdf"})


async def test_borrar(repo):
    document = await completed(repo)
    await DeleteDocumentUseCase(repo).execute(document.id)
    assert await ListDocumentsUseCase(repo).execute() == []


async def test_borrar_inexistente_da_not_found(repo):
    with pytest.raises(DocumentNotFoundError):
        await DeleteDocumentUseCase(repo).execute("no-existe")
