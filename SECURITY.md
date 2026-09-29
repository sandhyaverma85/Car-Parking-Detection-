# SECURITY.md — Smart Curb & Parking Intelligence Platform

This document describes the security controls implemented in this project and
recommendations for production deployment.

**Legend:**
- ✅ **Implemented** — control is active in the current codebase.
- 📋 **Recommended** — best practice for production; not yet implemented in the prototype.
- 🔲 **Planned** — will be implemented in a later phase.

---

## 1. Authentication

### JWT (JSON Web Tokens)
- ✅ Short-lived access tokens (default: 30 minutes, configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`).
- ✅ `HS256` algorithm with a strong secret key (minimum 32 characters, validated at startup).
- ✅ Tokens are validated server-side on every protected request.
- 📋 **Production:** Use RS256 (asymmetric) with a private key stored in a secrets manager.
- 📋 **Production:** Implement refresh tokens with secure HttpOnly cookies.

### Password Hashing
- ✅ Passwords are hashed with **Argon2** (via `argon2-cffi` / `passlib`).
- ✅ Plain-text passwords are **never stored** in the database or logs.
- ✅ Password fields are excluded from all API response schemas.

### Brute-Force Protection
- ✅ Login endpoint rate-limited (configurable via `LOGIN_RATE_LIMIT` — default 5 req/min per IP).
- 📋 **Production:** Add account lockout after N failed attempts.
- 📋 **Production:** Consider CAPTCHA for public login pages.

---

## 2. Authorization (RBAC)

- ✅ Three roles: `CITIZEN`, `OFFICER`, `ADMIN`.
- ✅ Role enforcement is **server-side** in FastAPI route dependencies — **not** only in the frontend.
- ✅ Citizens cannot access enforcement or analytics endpoints.
- ✅ Officers cannot manage cameras, zones, or users.
- ✅ Tests verify that unauthorized access returns 403 Forbidden.

---

## 3. Secrets Management

- ✅ All secrets (`JWT_SECRET`, `DATABASE_URL`, RTSP credentials, API keys) are stored in `.env`.
- ✅ `.env` is listed in `.gitignore` — **never committed to version control**.
- ✅ `.env.example` contains only placeholder values; safe to commit.
- ✅ Application validates at startup that secrets are not placeholder values (`CHANGE_ME`).
- 📋 **Production:** Use a secrets manager (AWS Secrets Manager, HashiCorp Vault, or GCP Secret Manager) instead of `.env` files.
- 📋 **Production:** Rotate JWT secret periodically and invalidate existing tokens.

---

## 4. CCTV / Camera Security

- ✅ RTSP URLs (which may contain credentials) are stored only in `.env` — never in the database or frontend.
- ✅ RTSP credentials are **never logged** (redacted by the logging middleware).
- ✅ Citizens receive only parking availability data — **not** raw camera streams.
- ✅ The AI engine communicates with the backend via HTTP POST, not directly to the database.
- 📋 **Production:** Store RTSP credentials in a secrets manager, not `.env`.
- 📋 **Production:** Use network segmentation to isolate CCTV cameras from the public internet.
- 📋 **Production:** Enable TLS/SRTP for RTSP streams where supported by cameras.

---

## 5. API Security

### CORS
- ✅ Configured to allow only explicitly listed origins (no wildcard `*` in production).
- ✅ Configured via `CORS_ORIGINS` environment variable.

### Input Validation
- ✅ All API inputs validated by Pydantic v2 models.
- ✅ Malformed requests return 422 Unprocessable Entity, not a stack trace.

### SQL Injection
- ✅ SQLAlchemy ORM with parameterized queries — raw SQL with user input is **never used**.

### Rate Limiting
- ✅ Login: 5 requests per IP per minute (configurable).
- ✅ General API: 60 requests per IP per minute (configurable).
- 📋 **Production:** Use a distributed rate limiter (Redis-backed) behind a load balancer.

### Error Handling
- ✅ Internal stack traces, SQL errors, and filesystem paths are **never** returned to clients.
- ✅ All errors return a safe, user-facing message.

---

## 6. Database Security

- ✅ SQLAlchemy ORM — no raw SQL string construction with user data.
- ✅ Application uses a dedicated database user (`parking_user`) with minimum required permissions.
- ✅ The database superuser/root account is **not used** by the application.
- ✅ No hardcoded database credentials.
- ✅ Connection pooling via SQLAlchemy async engine.
- ✅ PostGIS spatial indexes on geographic columns.
- ✅ Proper transaction handling (commit/rollback).
- 📋 **Production:** Enable PostgreSQL SSL (`sslmode=require`).
- 📋 **Production:** Encrypt the database volume at rest.
- 📋 **Production:** Restrict network access to PostgreSQL port (5432) to application servers only.

---

## 7. Evidence / File Security

- ✅ Evidence frames are stored **outside** the frontend's public/static directory.
- ✅ Evidence is served only via authenticated API endpoints — direct filesystem access is blocked.
- ✅ Filenames are generated safely (UUID-based) — no user-controlled filenames.
- ✅ File type and size are validated before storage.
- ✅ Path traversal is prevented by using safe path construction.
- 📋 **Production:** Encrypt evidence frames at rest.
- 📋 **Production:** Define and enforce a data-retention policy (e.g., auto-delete after 90 days).
- 📋 **Production:** Store evidence in object storage (S3-compatible) with server-side encryption.

---

## 8. Logging Security

- ✅ Structured JSON logging via `structlog`.
- ✅ Sensitive fields are **automatically redacted** before any log is written:
  - `password`, `password_hash`, `token`, `access_token`
  - `jwt_secret`, `api_key`, `rtsp_url`, `authorization`
  - RTSP URLs with embedded credentials (regex-based redaction)
- ✅ Log files use rotating file handler (10 MB max, 5 backups).
- 📋 **Production:** Ship logs to a centralized SIEM (Splunk, Elastic, Google Cloud Logging).
- 📋 **Production:** Set log retention policy and restrict log file access to the application user.

---

## 9. Privacy

- ✅ Citizens receive only parking availability data — no enforcement or vehicle tracking data.
- ✅ Evidence access is restricted to OFFICER and ADMIN roles.
- 📋 **Production:** Define a data minimization policy — store only what is necessary.
- 📋 **Production:** Implement face/license-plate blurring in evidence frames if not needed for enforcement.
- 📋 **Production:** Comply with applicable data-protection laws (India's DPDP Act 2023).
- 📋 **Production:** Define and enforce data-retention periods for all stored data.

---

## 10. Network / Deployment Security

- 📋 **Production:** Use HTTPS/TLS for all traffic (Nginx + Let's Encrypt or managed TLS).
- 📋 **Production:** Configure security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options).
- 📋 **Production:** Run the application behind a reverse proxy (Nginx).
- 📋 **Production:** Use a Web Application Firewall (WAF) for public-facing APIs.
- 📋 **Production:** Expose PostgreSQL only on localhost (`127.0.0.1:5432`) — never on `0.0.0.0`.
- 📋 **Production:** Use Docker secrets or a secrets manager instead of environment variables in containers.

---

## 11. Dependency Security

- 📋 **Production:** Run `pip audit` or `safety check` regularly to detect vulnerable dependencies.
- 📋 **Production:** Pin all dependency versions (already done in `requirements.txt`).
- 📋 **Production:** Set up automated dependency update alerts (Dependabot or Renovate).
- 📋 **Production:** Scan Docker images with Trivy or Snyk.

---

## 12. Reporting Security Issues

If you discover a security vulnerability in this project, please report it privately:

- **Email:** [your-security-contact@example.com]
- **Do not** open a public GitHub issue for security vulnerabilities.
- We will acknowledge the report within 48 hours and work to resolve it promptly.
