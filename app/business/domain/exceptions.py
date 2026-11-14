"""errores de negocio, no conocen http ni fastapi"""


class DomainError(Exception):
    """base de todos los errores de negocio"""


class DocumentNotFoundError(DomainError):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"no existe el documento '{document_id}'")
        self.document_id = document_id


class DuplicateDocumentError(DomainError):
    def __init__(self, checksum: str) -> None:
        super().__init__(f"ya existe un documento con checksum '{checksum}'")
        self.checksum = checksum


class ReservationNotFoundError(DomainError):
    """la reserva no existe, vencio o pertenece a otra saga"""

    def __init__(self, document_id: str) -> None:
        super().__init__(f"no hay una reserva pendiente '{document_id}' para esta saga")
        self.document_id = document_id
