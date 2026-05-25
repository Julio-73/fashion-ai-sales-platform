# Service Layer Standards

## Service Responsibilities

Services own use-case orchestration:

- Validate business preconditions that require state.
- Coordinate repositories, policies, integrations, transactions, and events.
- Enforce tenant context and authorization assumptions before data changes.
- Convert low-level infrastructure failures into application errors.
- Return DTOs or result objects, not ORM models.

## Service Design

- Name services after cohesive capabilities: `ClienteService`, `CrmPipelineService`, `AiSalesService`, `WhatsAppConversationService`.
- Prefer command/query objects for complex inputs.
- Keep services stateless except for injected dependencies.
- Keep methods focused on one use case.
- Extract domain policies when conditionals become reusable business rules.

## Service Pattern

```python
class ClienteService:
    def __init__(self, repository: ClienteRepository) -> None:
        self._repository = repository

    async def create_cliente(
        self,
        tenant: TenantContext,
        payload: ClienteCreateRequest,
    ) -> ClienteDTO:
        existing = await self._repository.get_by_phone(
            empresa_id=tenant.empresa_id,
            telefono=payload.telefono,
        )
        if existing:
            raise ConflictError("cliente_phone_exists")

        cliente = await self._repository.create(
            empresa_id=tenant.empresa_id,
            payload=payload,
        )
        return ClienteDTO.model_validate(cliente)
```

## Transaction Boundaries

- Put transaction boundaries around write use cases.
- Keep transactions short.
- Do not hold database transactions open while waiting on slow external APIs when avoidable.
- Use outbox or job dispatch patterns for post-commit side effects.

## Service Anti-Patterns

- Services that simply pass through to repositories without adding use-case meaning.
- Services that know SQLAlchemy session internals when a repository can own them.
- Services that accept or return untyped dicts.
- Services that mix unrelated domains into one giant class.

