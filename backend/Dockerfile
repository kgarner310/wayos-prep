# --- Build stage ---
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/build/deps -r requirements.txt

# --- Production stage ---
FROM python:3.12-slim

# Security: run as non-root
RUN groupadd -r wayos && useradd -r -g wayos -s /usr/sbin/nologin wayos

WORKDIR /app

# Copy deps from builder
COPY --from=builder /build/deps /usr/local/lib/python3.12/site-packages/

# Copy app code
COPY --chown=wayos:wayos . .

USER wayos

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
