# API Naming Conventions

## Modules

Use clear domain module names:

```text
auth
clientes
crm
conversaciones
whatsapp
ai_sales
analytics
catalogos
automatizaciones
integrations
```

Keep one naming language per module and API surface. If the product schema uses `empresa_id`, Spanish resource names are acceptable and should be consistent.

## Routes

- Use plural nouns for collections.
- Use UUID path parameters named after the entity.
- Use action verbs only for commands that are not standard CRUD.
- Keep paths stable and predictable.

Examples:

```text
/clientes/{cliente_id}
/crm/pipelines/{pipeline_id}/etapas
/conversaciones/{conversacion_id}/mensajes
/ai-sales/respuestas
/automatizaciones/{automatizacion_id}/ejecutar
```

## Python Objects

Use consistent suffixes:

```text
ClienteCreateRequest
ClienteUpdateRequest
ClienteResponse
ClienteDTO
ClienteService
ClienteRepository
ClienteNotFoundError
get_cliente_service
get_cliente_repository
```

## Errors

- Use stable machine-readable error codes.
- Keep human messages separate from error codes when localization may matter.
- Do not expose stack traces, SQL errors, provider secrets, or raw provider response bodies.

Example:

```json
{
  "error": {
    "code": "cliente_not_found",
    "message": "Cliente not found"
  }
}
```

