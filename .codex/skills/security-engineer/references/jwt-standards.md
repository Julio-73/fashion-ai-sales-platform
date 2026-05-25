# JWT Standards

## Access Tokens

Use JWT access tokens for short-lived API authentication.

Required claims:

- `sub`: user ID or service principal ID
- `iss`: trusted issuer
- `aud`: expected audience
- `exp`: expiration
- `iat`: issued-at
- `jti`: unique token ID
- `typ`: token type, such as `access`

Useful SaaS claims:

- `empresa_id` or active tenant ID when the token is tenant-scoped
- role or permission version
- session ID

## Validation

Every JWT validation must verify:

- signature
- algorithm allowlist
- issuer
- audience
- expiration
- token type
- subject
- revoked/session state when applicable

Do not decode JWTs without verification except for non-security debugging tools.

## Signing Keys

- Store signing keys in secret management, not source code.
- Support key rotation with `kid` when practical.
- Use strong algorithms and vetted libraries.
- Do not accept `none` algorithm or algorithm confusion.

## Token Lifetimes

- Keep access tokens short-lived.
- Keep refresh tokens longer-lived but revocable and rotated.
- Use different lifetimes for admin or high-risk sessions when needed.

## Token Storage

- Prefer secure, HTTP-only cookies for browser refresh tokens when the app architecture supports it.
- If access tokens are stored in memory on the frontend, ensure refresh flows are protected.
- Do not store long-lived tokens in localStorage for sensitive SaaS dashboards unless there is a documented risk acceptance.
- Never log tokens.

## JWT Anti-Patterns

- Permanent JWTs.
- Tokens with secrets or sensitive customer data in claims.
- Trusting frontend-decoded claims for authorization.
- Using JWT roles without checking current user/account state when permissions can change.
- Mixing access and refresh token use.

