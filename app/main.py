import logging
import sys
from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI

from app.config.settings import settings
from app.data.database.mongo_connection import connect, disconnect, get_database, ping
from app.data.models.document_model import DocumentModel
from app.infrastructure.consul_registry import ConsulRegistry, build_consul_client
from app.infrastructure.health import HealthReporter
from app.infrastructure.in_flight import in_flight
from app.infrastructure.instance import INSTANCE_ID
from app.presentation.error_handlers import register_error_handlers
from app.presentation.middlewares.body_size_limit import BodySizeLimitMiddleware
from app.presentation.middlewares.in_flight import InFlightMiddleware
from app.presentation.routers.document_router import router as document_router
from app.presentation.routers.health_router import router as health_router

# logs a stdout (12-factor xi)
logging.basicConfig(
    stream=sys.stdout,
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    await init_beanie(database=get_database(), document_models=[DocumentModel])
    app.state.health = HealthReporter(in_flight, {"mongodb": ping})
    registry = None
    consul_client = None
    if settings.consul_enabled:
        consul_client = build_consul_client(settings)
        registry = ConsulRegistry(settings, consul_client, INSTANCE_ID)
        registry.start()
    yield
    # cierre ordenado: primero salir de consul, despues cerrar mongo
    if registry:
        await registry.stop()
    if consul_client:
        await consul_client.aclose()
    await disconnect()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.service_name, version=settings.service_version, lifespan=lifespan)
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_size_bytes)
    app.add_middleware(InFlightMiddleware, counter=in_flight)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(document_router)
    return app


app = create_app()
