"""composicion: unico lugar que elige las implementaciones concretas"""

from app.config.settings import settings
from app.data.repositories.mongo_document_repository import MongoDocumentRepository
from app.presentation.controllers.document_controller import DocumentController
from app.use_cases.confirm_document import ConfirmDocumentUseCase
from app.use_cases.delete_document import DeleteDocumentUseCase
from app.use_cases.get_document import GetDocumentUseCase
from app.use_cases.list_documents import ListDocumentsUseCase
from app.use_cases.release_reservation import ReleaseReservationUseCase
from app.use_cases.reserve_document import ReserveDocumentUseCase
from app.use_cases.update_document import UpdateDocumentUseCase


def get_document_controller() -> DocumentController:
    repository = MongoDocumentRepository()
    return DocumentController(
        reserve=ReserveDocumentUseCase(repository, settings.reservation_ttl_seconds),
        confirm=ConfirmDocumentUseCase(repository),
        release=ReleaseReservationUseCase(repository),
        list_documents=ListDocumentsUseCase(repository),
        get_document=GetDocumentUseCase(repository),
        update_document=UpdateDocumentUseCase(repository),
        delete_document=DeleteDocumentUseCase(repository),
    )
