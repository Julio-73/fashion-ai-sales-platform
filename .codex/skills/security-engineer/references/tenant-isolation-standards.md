# Tenant Isolation Standards

## Tenant Rule

Every tenant-owned operation must be scoped by tenant context, preferably `empresa_id` in this project.

Tenant isolation must be enforced in:

- authentication context
- authorization policies
- service methods
- repositories
- SQL filters
- background jobs
- analytics queries
- exports
- webhooks
- audit events

## Tenant Context

Use a typed tenant context:

```python
class TenantContext(BaseModel):
    empresa_id: UUID
    user_id: UUID
    roles: list[str]
    permissions: set[str]
```

Resolve tenant context from authenticated membership, not from untrusted client input alone.

## Repository Safety

Tenant-owned repository methods must accept `empresa_id` explicitly and filter by it.

Unsafe:

```python
select(Customer).where(Customer.id == customer_id)
```

Safe:

```python
select(Customer).where(
    Customer.empresa_id == empresa_id,
    Customer.id == customer_id,
)
```

## Object Authorization

Object-level authorization must verify that:

- the user belongs to the tenant
- the object belongs to the tenant
- the user has permission for the action
- role restrictions are respected

## Tenant Isolation Tests

Test that:

- tenant A cannot read tenant B records
- update/delete queries include `empresa_id`
- analytics/export endpoints are tenant-scoped
- background jobs carry tenant context
- webhook events map to the correct tenant integration

