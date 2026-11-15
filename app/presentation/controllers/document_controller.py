from app.presentation.dto.request.confirm_request import ConfirmRequestDTO
from app.presentation.dto.request.reservation_request import ReservationRequestDTO
from app.presentation.dto.request.update_request import UpdateRequestDTO
from app.presentation.dto.response.document_response import DocumentResponseDTO
from app.presentation.dto.response.reservation_response import ReservationResponseDTO
from app.use_cases.confirm_document import ConfirmDocumentUseCase
from app.use_cases.delete_document import DeleteDocumentUseCase
from app.use_cases.get_document import GetDocumentUseCase
from app.use_cases.list_documents import ListDocumentsUseCase
from app.use_cases.release_reservation import ReleaseReservationUseCase
from app.use_cases.reserve_document import ReserveDocumentUseCase
from app.use_cases.update_document import UpdateDocumentUseCase


class DocumentController:
    """traduce entre http (dtos) y los casos de uso; los errores los traduce error_handlers"""

    def __init__(
        self,
        reserve: ReserveDocumentUseCase,
        confirm: ConfirmDocumentUseCase,
        release: ReleaseReservationUseCase,
        list_documents: ListDocumentsUseCase,
        get_document: GetDocumentUseCase,
        update_document: UpdateDocumentUseCase,
        delete_document: DeleteDocumentUseCase,
    ) -> None:
        self._reserve = reserve
        self._confirm = confirm
        self._release = release
        self._list_documents = list_documents
        self._get_document = get_document
        self._update_document = update_document
        self._delete_document = delete_document

    async def reserve(self, dto: ReservationRequestDTO) -> ReservationResponseDTO:
        document = await self._reserve.execute(dto.saga_id, dto.checksum, dto.filename)
        return ReservationResponseDTO.from_entity(document)

    async def confirm(self, document_id: str, dto: ConfirmRequestDTO) -> DocumentResponseDTO:
        document = await self._confirm.execute(document_id, dto.saga_id, dto.extracted_text)
        return DocumentResponseDTO.from_entity(document)

    async def release(self, document_id: str, saga_id: str) -> None:
        await self._release.execute(document_id, saga_id)

    async def get_all_documents(self, skip: int, limit: int) -> list[DocumentResponseDTO]:
        documents = await self._list_documents.execute(skip=skip, limit=limit)
        return [DocumentResponseDTO.from_entity(document) for document in documents]

    async def get_document_by_id(self, document_id: str) -> DocumentResponseDTO:
        document = await self._get_document.execute(document_id)
        return DocumentResponseDTO.from_entity(document)

    async def update_document(self, document_id: str, dto: UpdateRequestDTO) -> DocumentResponseDTO:
        # el contrato http dice custom_name, en el dominio el campo es filename
        fields = {"filename": dto.custom_name} if dto.custom_name is not None else {}
        document = await self._update_document.execute(document_id, fields)
        return DocumentResponseDTO.from_entity(document)

    async def delete_document(self, document_id: str) -> dict[str, str]:
        await self._delete_document.execute(document_id)
        return {"message": f"Documento '{document_id}' eliminado correctamente."}
