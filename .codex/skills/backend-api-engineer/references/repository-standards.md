# Repository Standards

## Repository Responsibilities

Repositories own persistence:

- Build database queries.
- Enforce tenant-scoped filters.
- Map persistence models to DTOs or domain objects when appropriate.
- Hide ORM/session details from services.
- Provide intention-revealing methods.

## Tenant-Safe Queries

Every tenant-owned query must include `empresa_id`.

Unsafe:

```python
await session.get(ClienteModel, cliente_id)
```

Safe:

```python
stmt = select(ClienteModel).where(
    ClienteModel.empresa_id == empresa_id,
    ClienteModel.id == cliente_id,
)
```

Apply this to reads, updates, deletes, joins, counts, exports, analytics, and background jobs.

## Repository Method Names

Use methods that describe product intent:

```python
get_by_id
get_by_phone
list_by_segment
list_open_conversations
create_opportunity
mark_message_delivered
record_ai_interaction
```

Avoid generic `query`, `run`, `execute`, or leaking query builders.

## SQLAlchemy Async Pattern

```python
class ClienteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, *, empresa_id: UUID, cliente_id: UUID) -> ClienteModel | None:
        stmt = select(ClienteModel).where(
            ClienteModel.empresa_id == empresa_id,
            ClienteModel.id == cliente_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
```

## Repository Tests

- Verify `empresa_id` filters.
- Verify not-found behavior.
- Verify unique constraints and foreign key behavior.
- Verify pagination and ordering for list queries.
- Verify write methods persist expected fields and audit timestamps.

