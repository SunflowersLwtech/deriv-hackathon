# ─── TradeIQ Backend ───────────────────────────────────────
# Django + Channels (Daphne ASGI) for HTTP + WebSocket
# Multi-stage build for smaller production image
# ───────────────────────────────────────────────────────────

# --- Stage 1: Build dependencies ---
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for psycopg2 compilation
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt gunicorn whitenoise

# --- Stage 2: Production runtime ---
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Runtime deps only (no gcc needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r tradeiq && useradd -r -g tradeiq tradeiq && \
    mkdir -p /app/staticfiles && chown -R tradeiq:tradeiq /app

# Collect static files (Django admin / DRF browsable API)
RUN DJANGO_SECRET_KEY=build-placeholder \
    DATABASE_URL="" \
    python manage.py collectstatic --noinput 2>/dev/null || true

USER tradeiq

EXPOSE 8000

# Daphne for ASGI (supports HTTP + WebSocket)
# Use $PORT for cloud platforms (Railway, Render) that inject PORT env var
# 1. Run migrations
# 2. Seed demo data (idempotent — safe to run repeatedly)
# 3. Warm demo cache in background (pre-computes Trading Twin, multi-persona)
# 4. Start Daphne ASGI server
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_demo --quiet 2>/dev/null || true && python manage.py warm_demo_cache 2>/dev/null & daphne -b 0.0.0.0 -p ${PORT:-8000} tradeiq.asgi:application"]
