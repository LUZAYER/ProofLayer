# ProofLayer Gateway & Backend Services
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY services/ ./services/
COPY policies/ ./policies/
COPY eval/ ./eval/
COPY scripts/ ./scripts/
COPY sdk/ ./sdk/
COPY pyproject.toml .

# Create logs directory for ledger
RUN mkdir -p logs eval/out

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "services.gateway.app:app", "--host", "0.0.0.0", "--port", "8000"]
