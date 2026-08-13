FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Default: run with mock repositories enabled
ENV USE_MOCK_REPOSITORIES=true
ENV LOG_LEVEL=INFO

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
