"""endpoints internos de documentos (/api/v1/documents), solo los llama el orquestador"""

from fastapi import APIRouter, Depends, Query, Response, status

from app.config.settings import settings
from app.dependencies import get_document_controller
from app.presentation.controllers.document_controller import DocumentController
from app.presentation.dto.request.confirm_request import ConfirmRequestDTO
from app.presentation.dto.request.reservation_request import ReservationRequestDTO
from app.presentation.dto.request.update_request import UpdateRequestDTO
from app.presentation.dto.response.document_response import DocumentResponseDTO
from app.presentation.dto.response.reservation_response import ReservationResponseDTO

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


# pasos de la saga

@router.post(
    "/reservations",
    response_model=ReservationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Reservar un checksum (paso de la saga)",
)
async def reserve(
    dto: ReservationRequestDTO,
    controller: DocumentController = Depends(get_document_controller),
) -> ReservationResponseDTO:
    """crea un documento pendiente; 409 si el checksum ya existe"""
    return await controller.reserve(dto)


@router.put(
    "/{document_id}/content",
    response_model=DocumentResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Confirmar una reserva con el texto (paso de la saga)",
)
async def confirm(
    document_id: str,
    dto: ConfirmRequestDTO,
    controller: DocumentController = Depends(get_document_controller),
) -> DocumentResponseDTO:
    """guarda el texto y completa el documento; 404 si la reserva no existe o vencio"""
    return await controller.confirm(document_id, dto)


@router.delete(
    "/reservations/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Liberar una reserva (compensacion de la saga)",
)
async def release(
    document_id: str,
    saga_id: str = Query(..., min_length=1, max_length=64),
    controller: DocumentController = Depends(get_document_controller),
) -> Response:
    """idempotente: siempre 204, exista o no la reserva"""
    await controller.release(document_id, saga_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# crud de documentos completados

@router.get(
    "",
    response_model=list[DocumentResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar documentos (paginado)",
)
async def get_all_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    controller: DocumentController = Depends(get_document_controller),
) -> list[DocumentResponseDTO]:
    return await controller.get_all_documents(skip=skip, limit=limit)


@router.get(
    "/{document_id}",
    response_model=DocumentResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obtener un documento",
)
async def get_document_by_id(
    document_id: str,
    controller: DocumentController = Depends(get_document_controller),
) -> DocumentResponseDTO:
    return await controller.get_document_by_id(document_id)


@router.put(
    "/{document_id}",
    response_model=DocumentResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Renombrar un documento",
)
async def update_document(
    document_id: str,
    dto: UpdateRequestDTO,
    controller: DocumentController = Depends(get_document_controller),
) -> DocumentResponseDTO:
    return await controller.update_document(document_id, dto)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar un documento",
)
async def delete_document(
    document_id: str,
    controller: DocumentController = Depends(get_document_controller),
) -> dict[str, str]:
    return await controller.delete_document(document_id)
