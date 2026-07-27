FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps (minimal — no ML framework needed for orchestration)
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Application
COPY scripts/ ./scripts/
COPY cases/ ./cases/
COPY models/ ./models/
COPY policies/ ./policies/
COPY docs/ ./docs/

# Non-root user
RUN useradd --create-home appuser
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["python3", "scripts/open_djicht_api.py", "--port", "8080"]
