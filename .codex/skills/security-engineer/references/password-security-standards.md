# Password Security Standards

## Hashing

- Hash passwords with Argon2id or bcrypt through a vetted library.
- Use per-password salts supplied by the library.
- Never store plaintext passwords.
- Never log passwords.
- Never return password hashes from APIs.
- Keep hash parameters configurable for future upgrades.

## Password Verification

- Use constant-time verification through the password library.
- Rehash on login when parameters are outdated.
- Return generic errors for login failures.
- Apply brute-force protection.

## Password Policy

Use a pragmatic policy:

- minimum length
- breached/common password checks when available
- no password reuse for recent passwords when required
- no composition rules that create weak predictable passwords

## Reset Flows

Password reset tokens must:

- be random, high entropy, and single-use
- be stored hashed server-side
- expire quickly
- not reveal whether an account exists
- revoke active sessions after reset when appropriate

## Brute-Force Protection

Protect:

- login attempts
- password reset requests
- password reset submission
- MFA verification if added later

Use rate limits by IP, user/email, tenant, and endpoint where practical.

