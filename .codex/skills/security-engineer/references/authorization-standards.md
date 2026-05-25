# Authorization Standards

## Authorization Model

Support current roles while allowing future RBAC expansion:

- owner
- admin
- manager
- sales_agent
- analyst
- integration_admin
- support

Keep permissions explicit and action-oriented:

```text
customers:read
customers:write
crm:manage
conversations:reply
whatsapp:manage
ai:configure
analytics:read
users:manage
settings:manage
```

## Policy Pattern

Use reusable policies or dependencies:

```python
def require_permission(permission: str) -> Callable[..., TenantContext]:
    ...
```

Policies should verify:

- authenticated user
- active account
- tenant membership
- required permission
- object ownership when applicable

## Protected Dashboards

Frontend dashboard protection must be backed by API protection.

Protected dashboard routes should:

- require authenticated session
- require tenant selection or membership
- hide or disable unauthorized actions
- handle permission-denied states

API endpoints must still enforce the same permissions server-side.

## Admin Actions

High-impact actions require stricter checks:

- role changes
- invitations
- integration credential changes
- AI automation configuration
- data export
- tenant settings
- user deactivation

Audit these actions with actor, tenant, target, action, timestamp, and request ID.

## Authorization Anti-Patterns

- Checking only that a user is logged in.
- Trusting frontend hidden buttons.
- Using roles directly everywhere instead of permission policies.
- Missing object-level checks.
- Allowing admin routes to skip tenant scope.

