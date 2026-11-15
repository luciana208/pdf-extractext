# pdf-extractext

Microservicio de **persistencia** de PDF-extractext. Es el único que habla con MongoDB: guarda los documentos con su checksum y su texto, ofrece el CRUD y ejecuta los pasos de la Saga que tocan datos (reservar, confirmar y liberar).

Este repo era el monolito de la Etapa 1. En la Etapa 2 se quedó con la responsabilidad de persistir; la validación, la extracción y la API pública pasaron a sus propios servicios.

## Endpoints (internos, los llama el orquestador)

Base: `/api/v1/documents`

| Método | Ruta | Descripción | OK | Errores |
|---|---|---|---|---|
| `POST` | `/reservations` | Reserva un checksum: `{"saga_id", "checksum", "filename"}` | `201` | `409` duplicado, `422` |
| `PUT` | `/{id}/content` | Confirma la reserva con el texto: `{"saga_id", "extracted_text"}` | `200` | `404` reserva inexistente o vencida |
| `DELETE` | `/reservations/{id}?saga_id=` | Compensación: libera la reserva | `204` siempre | — |
| `GET` | `?skip&limit` | Lista paginada de documentos completados | `200` | `422` |
| `GET` | `/{id}` | Un documento | `200` | `404` |
| `PUT` | `/{id}` | Renombra: `{"custom_name"}` | `200` | `404` |
| `DELETE` | `/{id}` | Borra | `200` | `404` |

`GET /health` informa el estado de `mongodb` en `dependencies`.

## Reservas y duplicados

- Una reserva es un documento con `status: pending`, `saga_id` y `expires_at`. El CRUD no la ve.
- El **índice único** sobre `checksum` impide duplicados aunque lleguen dos subidas al mismo tiempo.
- El **índice TTL** sobre `expires_at` borra solo las reservas que nunca se confirmaron (por ejemplo, si el orquestador se cayó en medio de la Saga). Los documentos completados tienen `expires_at: null` y nunca vencen.
- **Idempotencia:** reservar dos veces con el mismo `saga_id` devuelve la misma reserva; confirmar dos veces devuelve el mismo documento; liberar algo que no existe responde `204`. Así los reintentos no rompen nada.

## Arquitectura

```
presentation   document_router · controller · DTOs de reserva, confirmacion y CRUD · errores RFC 9457
use_cases      Reserve · Confirm · ReleaseReservation · List · Get · Update · Delete
business       Document (pending/completed) · excepciones · puerto IDocumentRepository
data           MongoDocumentRepository (Beanie 2 + PyMongo async) · DocumentModel con indices
infrastructure Consul · tags de Traefik · health · instancia
```

## Configuración

Ver `.env.example`. Las propias de este servicio:

| Variable | Por defecto | Descripción |
|---|---|---|
| `MONGO_URL` | `mongodb://localhost:27017` | URL de MongoDB |
| `DB_NAME` | `pdf_extraction_db` | Base de datos |
| `MONGO_CONNECT_RETRIES` | `10` | Intentos de conexión al arrancar (espera creciente) |
| `RESERVATION_TTL_SECONDS` | `300` | Vida de una reserva sin confirmar |
| `DEFAULT_PAGE_SIZE` / `MAX_PAGE_SIZE` | `20` / `100` | Paginación |
| `MAX_BODY_SIZE_MB` | `30` | Límite del body (el texto extraído puede ser grande) |

## Desarrollo

```bash
uv sync
uv run pytest tests/unit                                   # sin MongoDB
MONGO_URL=mongodb://localhost:27017 uv run pytest          # todo, con MongoDB
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from tests
```

Los tests de integración usan la base `pdf_test_db` para no tocar los datos de desarrollo.

## Plataforma (igual en los cuatro servicios)

| Pieza | Archivo | Qué hace |
|---|---|---|
| Registro en Consul | `app/infrastructure/consul_registry.py` | Al arrancar registra la instancia con ID único (`<servicio>-<hex>`), su IP, el check HTTP a `/health` y los tags de Traefik. Si Consul no está, reintenta en segundo plano. Al apagarse se da de baja. |
| Tags de Traefik | `app/infrastructure/traefik_tags.py` | Routers interno y público, circuit breaker y reintentos |
| Health | `app/infrastructure/health.py` | Contrato común: `status`, `service`, `version`, `instance_id`, `uptime_seconds`, `memory_mb`, `requests_in_flight`, `dependencies` |
| Errores | `app/presentation/error_handlers.py` | Todo error sale en formato RFC 9457 (`application/problem+json`) |

## Ejecución dentro del sistema completo

Este servicio no se levanta solo en producción: lo levanta `pdf-extractext-deploy` junto con Traefik, Consul y el resto de los servicios.

```bash
cd ../pdf-extractext-deploy
./scripts/up.sh
```

## Imagen Docker

- Multi-stage: `uv` solo está en la etapa de build; la imagen final tiene Python 3.14 slim, el venv y el código.
- Usuario sin privilegios (`appuser`) y zona horaria `America/Argentina/Buenos_Aires`.
- `HEALTHCHECK` contra `/health`.
- Granian toma host, puerto y workers de `GRANIAN_*`, así que el puerto no queda fijo en la imagen.

```bash
docker build -t pdf-extractext/documents:1.0.0 .
```

## Principios aplicados

- **Arquitectura limpia / puertos y adaptadores:** el negocio depende de interfaces y `app/dependencies.py` elige las implementaciones.
- **SOLID, DRY, KISS, YAGNI:** un caso de uso por operación, sin dependencias que no se usan.
- **TDD:** cada cambio arranca con un test que falla.
- **12-Factor:** un repo por servicio (I), dependencias fijadas con `uv.lock` (II), configuración por entorno (III), servicios externos por URL (IV), build y run separados (V), procesos sin estado (VI), port binding (VII), apagado ordenado (IX), logs a stdout (XI).

## Equipo

Fabio, Luciana y Celina — Desarrollo de Software, UTN Facultad Regional San Rafael, 2026.

## Licencia

MIT, ver [LICENSE](LICENSE).
