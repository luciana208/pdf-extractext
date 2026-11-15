from abc import ABC, abstractmethod

from app.business.entities.document import Document


class IDocumentRepository(ABC):
    """
    contrato de persistencia. las consultas del crud solo ven documentos completados;
    "no existe" se devuelve como None (o False) y el caso de uso decide si es error.
    """

    @abstractmethod
    async def save(self, document: Document) -> Document:
        """persiste un documento nuevo; lanza DuplicateDocumentError si el checksum ya existe"""

    @abstractmethod
    async def get_by_checksum(self, checksum: str) -> Document | None:
        """documento con ese checksum en cualquier estado"""

    @abstractmethod
    async def complete(self, document_id: str, saga_id: str, extracted_text: str) -> Document | None:
        """pasa una reserva pendiente de esa saga a completada; None si no hay reserva"""

    @abstractmethod
    async def delete_reservation(self, document_id: str, saga_id: str) -> bool:
        """borra la reserva pendiente de esa saga; False si no existia"""

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Document]:
        """documentos completados paginados"""

    @abstractmethod
    async def get_by_id(self, document_id: str) -> Document | None:
        """documento completado con ese id"""

    @abstractmethod
    async def update(self, document_id: str, fields: dict) -> Document | None:
        """actualiza metadatos (solo filename) de un documento completado"""

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """borra un documento completado"""
