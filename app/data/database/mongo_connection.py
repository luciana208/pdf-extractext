"""conexion a mongodb con el driver async de pymongo, un cliente por proceso"""

import asyncio
import logging

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import PyMongoError

from app.config.settings import settings

logger = logging.getLogger(__name__)

_client: AsyncMongoClient | None = None
_database: AsyncDatabase | None = None


async def connect() -> None:
    """abre la conexion y reintenta con espera creciente si mongo todavia no arranco"""
    global _client, _database
    _client = AsyncMongoClient(
        settings.mongo_url,
        serverSelectionTimeoutMS=5000,
        retryWrites=True,
        retryReads=True,
        tz_aware=True,
    )
    delay = 1
    for attempt in range(1, settings.mongo_connect_retries + 1):
        try:
            await _client.admin.command("ping")
            break
        except PyMongoError as exc:
            if attempt == settings.mongo_connect_retries:
                logger.error("no se pudo conectar a mongodb: %s", exc)
                raise
            logger.warning("mongodb no responde (intento %s), reintento en %ss", attempt, delay)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 10)
    _database = _client[settings.db_name]
    logger.info("conexion a mongodb establecida (%s)", settings.db_name)


async def disconnect() -> None:
    global _client, _database
    if _client:
        await _client.close()
        logger.info("conexion a mongodb cerrada")
    _client = None
    _database = None


def get_database() -> AsyncDatabase:
    if _database is None:
        raise RuntimeError("la base de datos no esta inicializada, falta connect()")
    return _database


async def ping() -> bool:
    # chequeo para el health
    if _client is None:
        return False
    await _client.admin.command("ping")
    return True
