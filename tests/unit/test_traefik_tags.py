from app.config.settings import Settings
from app.infrastructure.traefik_tags import build_traefik_tags


def test_router_interno_con_circuit_breaker_y_reintentos():
    tags = build_traefik_tags(Settings(router_name="documents", internal_host="documents.internal", public_host=""))
    assert "traefik.enable=true" in tags
    assert "traefik.http.routers.documents-internal.rule=Host(`documents.internal`)" in tags
    assert "traefik.http.routers.documents-internal.entrypoints=internal" in tags
    assert "traefik.http.routers.documents-internal.middlewares=documents-cb,documents-retry" in tags
    assert any(tag.startswith("traefik.http.middlewares.documents-cb.circuitbreaker.expression=") for tag in tags)
    assert "traefik.http.middlewares.documents-retry.retry.attempts=3" in tags


def test_sin_host_publico_no_hay_router_https():
    tags = build_traefik_tags(Settings(router_name="documents", public_host=""))
    assert not any(".routers.documents.rule" in tag for tag in tags)


def test_con_host_publico_agrega_router_https_con_tls():
    tags = build_traefik_tags(Settings(router_name="documents", public_host="documents.pdfextractext.localhost"))
    assert "traefik.http.routers.documents.entrypoints=https" in tags
    assert "traefik.http.routers.documents.tls=true" in tags
