# Validation Standards

## Validation Boundaries

Validate:

- request body
- path parameters
- query parameters
- headers
- cookies
- JWT claims
- refresh token records
- webhook signatures and payloads
- environment settings
- provider configuration

## Pydantic Standards

- Use Pydantic schemas for auth requests, token responses, refresh requests, password reset, role changes, and provider payloads.
- Use strict types where practical.
- Use `UUID`, `EmailStr`, constrained strings, enums/literals, and timezone-aware datetimes.
- Reject unknown or unsafe fields on security-sensitive payloads when appropriate.

## Server-Side Authority

Client validation improves UX but never establishes trust.

Server-side validation must enforce:

- identity
- tenant membership
- permissions
- object ownership
- password policy
- token type and status
- provider signature validity
- integration ownership

## Secure Error Handling

- Return stable error codes.
- Keep auth failures generic where detail would aid attackers.
- Do not leak whether reset tokens, users, or provider secrets exist.
- Log useful internal detail with redaction.

## Validation Anti-Patterns

- Trusting frontend route guards.
- Trusting decoded JWT claims without verification.
- Trusting tenant IDs from the request body.
- Accepting raw webhook payloads as application commands.
- Letting provider data bypass internal validation.

