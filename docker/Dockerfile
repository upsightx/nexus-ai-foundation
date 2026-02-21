FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    pydantic \
    pydantic-settings \
    httpx \
    aiohttp \
    loguru \
    python-dotenv

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "-m", "uvicorn", "nexus.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
