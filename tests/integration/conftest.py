"""
fixtures de integracion: http -> router -> caso de uso -> repositorio -> mongodb real.
necesitan mongodb en MONGO_URL (o docker-compose.test.yml).
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.data.models.document_model import DocumentModel
from app.main import create_app


@pytest_asyncio.fixture
async def client():
    app = create_app()
    # el lifespan conecta a mongo e inicializa beanie
    async with app.router.lifespan_context(app):
        await DocumentModel.delete_all()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
            yield http_client
        await DocumentModel.delete_all()
