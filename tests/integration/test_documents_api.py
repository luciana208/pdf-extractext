import asyncio

from app.data.models.document_model import DocumentModel

URL = "/api/v1/documents"
CHECKSUM = "c" * 64
OTHER_CHECKSUM = "d" * 64


async def reserve(client, saga_id="saga-1", checksum=CHECKSUM, filename="informe.pdf"):
    return await client.post(f"{URL}/reservations", json={"saga_id": saga_id, "checksum": checksum, "filename": filename})


async def create_completed(client, saga_id="saga-1", checksum=CHECKSUM, text="texto del pdf"):
    reservation = (await reserve(client, saga_id, checksum)).json()
    response = await client.put(f"{URL}/{reservation['id']}/content", json={"saga_id": saga_id, "extracted_text": text})
    return response.json()


async def test_reserva_devuelve_201_pendiente_con_vencimiento(client):
    response = await reserve(client)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["expires_at"]


async def test_reserva_duplicada_devuelve_409_problem_json(client):
    await create_completed(client)
    response = await reserve(client, saga_id="saga-2")
    assert response.status_code == 409
    assert response.headers["content-type"] == "application/problem+json"


async def test_reservas_simultaneas_solo_una_gana(client):
    responses = await asyncio.gather(*(reserve(client, saga_id=f"saga-{n}") for n in range(5)))
    assert sorted(r.status_code for r in responses) == [201, 409, 409, 409, 409]


async def test_checksum_invalido_devuelve_422(client):
    response = await client.post(f"{URL}/reservations", json={"saga_id": "s", "checksum": "corto", "filename": "a.pdf"})
    assert response.status_code == 422


async def test_confirmar_devuelve_el_documento_completo(client):
    document = await create_completed(client, text="hola mundo")
    assert document["extracted_text"] == "hola mundo"
    assert document["text_preview"] == "hola mundo"
    assert document["name"] == "informe.pdf"


async def test_confirmar_con_otra_saga_devuelve_404(client):
    reservation = (await reserve(client)).json()
    response = await client.put(f"{URL}/{reservation['id']}/content", json={"saga_id": "otra", "extracted_text": "x"})
    assert response.status_code == 404


async def test_compensacion_borra_la_reserva_y_permite_reintentar(client):
    reservation = (await reserve(client)).json()
    response = await client.delete(f"{URL}/reservations/{reservation['id']}", params={"saga_id": "saga-1"})
    assert response.status_code == 204
    assert (await reserve(client, saga_id="saga-2")).status_code == 201


async def test_compensacion_es_idempotente(client):
    response = await client.delete(f"{URL}/reservations/{'0' * 24}", params={"saga_id": "saga-1"})
    assert response.status_code == 204


async def test_listado_no_incluye_pendientes(client):
    await create_completed(client)
    await reserve(client, saga_id="saga-2", checksum=OTHER_CHECKSUM)
    response = await client.get(URL)
    assert response.status_code == 200
    assert [d["checksum"] for d in response.json()] == [CHECKSUM]


async def test_crud_completo(client):
    document = await create_completed(client)
    document_id = document["id"]

    assert (await client.get(f"{URL}/{document_id}")).json()["id"] == document_id

    renamed = await client.put(f"{URL}/{document_id}", json={"custom_name": "nuevo.pdf"})
    assert renamed.json()["name"] == "nuevo.pdf"

    assert (await client.delete(f"{URL}/{document_id}")).status_code == 200
    assert (await client.get(f"{URL}/{document_id}")).status_code == 404


async def test_id_invalido_devuelve_404(client):
    assert (await client.get(f"{URL}/no-es-un-object-id")).status_code == 404


async def test_indice_ttl_creado(client):
    indexes = await DocumentModel.get_pymongo_collection().index_information()
    assert indexes["reservation_ttl"]["expireAfterSeconds"] == 0
    assert indexes["checksum_unique"]["unique"] is True


async def test_health_informa_mongodb(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["dependencies"] == {"mongodb": "ok"}
