from datetime import datetime, timedelta, timezone

from app.business.entities.document import Document, DocumentStatus

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)


def test_por_defecto_es_completado_y_sin_id():
    document = Document(filename="a.pdf", checksum="x")
    assert document.status == DocumentStatus.COMPLETED
    assert not document.is_persisted()
    assert not document.is_pending()


def test_reserva_vencida():
    document = Document(filename="a.pdf", checksum="x", status=DocumentStatus.PENDING, expires_at=NOW - timedelta(seconds=1))
    assert document.is_expired_reservation(NOW)


def test_reserva_vigente_no_esta_vencida():
    document = Document(filename="a.pdf", checksum="x", status=DocumentStatus.PENDING, expires_at=NOW + timedelta(minutes=1))
    assert not document.is_expired_reservation(NOW)


def test_un_completado_nunca_esta_vencido():
    document = Document(filename="a.pdf", checksum="x", expires_at=NOW - timedelta(days=1))
    assert not document.is_expired_reservation(NOW)


def test_pertenece_a_la_saga():
    document = Document(filename="a.pdf", checksum="x", saga_id="s1")
    assert document.belongs_to("s1")
    assert not document.belongs_to("s2")
