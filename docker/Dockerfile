FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml requirements.txt README.md /app/
COPY src/ /app/src/
COPY forecastos/ /app/forecastos/
COPY dashboard/ /app/dashboard/

# Install python packages
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic pandas numpy matplotlib sqlalchemy httpx python-multipart
RUN pip install --no-cache-dir -e .

EXPOSE 8000

ENV TIMESFM_MOCK=true
ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["python", "-m", "forecastos.api.main"]
