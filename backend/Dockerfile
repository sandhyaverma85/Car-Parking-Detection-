# =============================================================================
# Backend Dockerfile — multi-stage build
# =============================================================================

# ── Stage 1: Build dependencies ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System packages needed to compile some Python wheels (e.g., asyncpg, argon2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app/ ./app/

# Evidence directory — will be mounted as a Docker volume in production
RUN mkdir -p /evidence /logs \
    && chown -R appuser:appgroup /app /evidence /logs

USER appuser

# Expose the application port (actual binding configured via env/compose)
EXPOSE 8000

# Uvicorn in production mode (single worker; use Gunicorn+Uvicorn workers for multi-core)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
