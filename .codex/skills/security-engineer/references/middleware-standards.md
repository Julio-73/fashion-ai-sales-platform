# Middleware Standards

## Middleware Responsibilities

Middleware may handle:

- request IDs and correlation IDs
- structured logging context
- security headers
- CORS policy
- trusted host validation
- body size limits
- rate limit integration
- timing metrics

Middleware should not contain business authorization logic that depends on route-specific resources.

## Security Headers

Configure security headers appropriate for the deployment:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy`
- `Content-Security-Policy` where the frontend deployment supports it
- `Strict-Transport-Security` behind HTTPS
- frame protections through CSP or equivalent headers

## CORS

- Use explicit allowed origins.
- Do not use wildcard origins with credentials.
- Keep dev origins separate from production settings.
- Validate CORS configuration through environment settings.

## Rate Limiting

Rate-limit:

- login
- password reset
- token refresh
- public webhooks when feasible
- AI endpoints
- WhatsApp sending endpoints
- exports/imports
- automation triggers

Apply identity-aware limits where possible: IP, user ID, tenant ID, endpoint, and provider.

## Middleware Anti-Patterns

- Swallowing exceptions and returning inconsistent errors.
- Logging request bodies that may include credentials or tokens.
- Adding auth state through mutable globals.
- Applying CORS broadly because it is convenient.
- Performing slow network calls in middleware.

