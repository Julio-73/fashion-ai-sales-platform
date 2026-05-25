# Validation Standards

## Pydantic Boundaries

Use Pydantic schemas for:

- Request bodies.
- Query parameter groups.
- Response models.
- Service command objects.
- DTOs crossing application boundaries.
- Provider webhook normalization.
- Settings/configuration.

## Strict Typing

- Type every public function and method.
- Avoid `dict`, `list`, and `Any` without type parameters.
- Prefer `UUID`, `EmailStr`, constrained strings, enums/literals, decimals, and timezone-aware datetimes.
- Normalize provider payloads immediately into typed internal models.

## Request Schema Pattern

```python
class ClienteCreateRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    telefono: str = Field(min_length=8, max_length=32)
    email: EmailStr | None = None
    segmento_ids: list[UUID] = Field(default_factory=list)
```

## Response Schema Pattern

```python
class ClienteResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre: str
    telefono: str
    email: EmailStr | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

## Validation Rules

- Validate shape at the API boundary.
- Validate stateful business rules in services or domain policies.
- Validate external provider signatures before parsing trusted commands.
- Validate tenant access before repository calls.
- Validate response models to prevent leaking internal fields.

## Validation Anti-Patterns

- Untyped request dictionaries.
- Manual validation scattered across routers.
- Returning internal database models as API responses.
- Accepting provider webhook payloads as trusted application commands.
- Silently coercing critical identifiers or money values.

