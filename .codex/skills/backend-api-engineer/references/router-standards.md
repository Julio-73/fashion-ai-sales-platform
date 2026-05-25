# Router Standards

## Router Responsibilities

Routers may:

- Declare route paths, methods, status codes, tags, and response models.
- Accept validated request data.
- Resolve dependencies.
- Check endpoint-level authorization when appropriate.
- Call one service method.
- Convert service results into response schemas.

Routers must not:

- Query the database directly.
- Call external provider SDKs directly.
- Contain business workflows.
- Duplicate validation already owned by schemas or domain policies.
- Build giant conditional flows.

## Route Shape

Prefer clear resource-oriented paths:

```text
GET    /api/v1/clientes
POST   /api/v1/clientes
GET    /api/v1/clientes/{cliente_id}
PATCH  /api/v1/clientes/{cliente_id}
GET    /api/v1/conversaciones/{conversacion_id}/mensajes
POST   /api/v1/conversaciones/{conversacion_id}/respuestas-ai
```

Use action endpoints only for real commands:

```text
POST /api/v1/automatizaciones/{automation_id}/ejecutar
POST /api/v1/whatsapp/webhooks/messages
POST /api/v1/oportunidades/{oportunidad_id}/cerrar
```

## Router Function Pattern

```python
@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    payload: ClienteCreateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    service: ClienteService = Depends(get_cliente_service),
) -> ClienteResponse:
    result = await service.create_cliente(tenant=tenant, payload=payload)
    return ClienteResponse.model_validate(result)
```

## Response Rules

- Use typed response schemas for success responses.
- Use consistent error schemas through exception handlers.
- Do not leak internal exception text, SQL errors, provider payloads, or secrets.
- Return `202 Accepted` for async jobs and include a tracking identifier.

