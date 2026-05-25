# Authentication Standards

## Authentication Architecture

- Keep authentication logic in an auth module or core security module.
- Separate credential verification, token issuing, refresh token management, and user/account lookup.
- Do not mix authentication with route business logic.
- Use dependency injection for authentication context in protected routes.
- Model authentication events for auditability.

## Required Flows

Support:

- registration or invitation acceptance
- login
- access token issuance
- refresh token rotation
- logout
- revoke all sessions
- password reset
- password change
- account lock or throttling after abuse

## Auth Service Responsibilities

The auth service may:

- verify credentials
- check account status
- issue access and refresh tokens
- rotate refresh tokens
- revoke token families
- record auth audit events
- raise stable auth errors

The auth service must not:

- return password hashes
- leak whether sensitive reset tokens exist
- bypass tenant membership checks for dashboard access
- create ad hoc token payloads in routers

## Account State

Track account states explicitly:

- active
- invited
- disabled
- locked
- pending_email_verification when required

Protected routes must reject disabled or locked users.

## Audit Events

Record security events for:

- login success/failure
- token refresh
- refresh token reuse detection
- logout/revocation
- password reset requested/completed
- role or permission changes
- tenant membership changes

