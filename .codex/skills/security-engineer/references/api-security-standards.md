# API Security Standards

## Route Protection

- Mark public routes explicitly.
- Require auth dependencies on all protected routes.
- Require permission dependencies on admin, tenant management, CRM mutation, WhatsApp sending, AI automation, export, and billing-like endpoints.
- Keep route handlers thin and delegate security decisions to reusable dependencies, policies, and services.

## Request And Response Safety

- Validate request bodies, path params, query params, and headers.
- Return typed responses.
- Do not return password hashes, refresh tokens, internal tokens, provider secrets, or raw secret-bearing payloads.
- Use consistent error payloads without leaking stack traces or SQL/provider internals.

## Webhooks

For WhatsApp and provider webhooks:

- verify provider signature
- validate timestamp/replay protection when supported
- store idempotency keys/provider event IDs
- normalize payloads into typed schemas
- process slow work asynchronously
- never trust provider payload tenant mapping without verification against stored integration configuration

## API Keys And Service Tokens

If service tokens are needed:

- store hashed token material server-side
- scope by tenant, integration, and permissions
- support expiration and revocation
- show secrets only once
- audit creation, use, and revocation

## Logging

- Log request IDs, user IDs, tenant IDs, endpoint, status, latency, and stable error codes.
- Redact authorization headers, cookies, passwords, tokens, API keys, phone numbers where appropriate, and sensitive customer data.

## API Security Anti-Patterns

- Relying on frontend route guards only.
- Protecting dashboards but leaving API endpoints open.
- Returning raw provider errors to clients.
- Missing authorization on update/delete/export endpoints.
- Long-running AI or integration calls inside protected request paths without timeouts.

