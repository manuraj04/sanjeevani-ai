FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user

WORKDIR /app

# Ultra-slim cloud runtime (~110 MB RSS RAM, fits cleanly inside 512 MB Free Tier containers)
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-cloud.txt

COPY src/__init__.py src/config.py ./src/
COPY src/api/ ./src/api/
COPY data/processed/sanjeevani_kb.db ./data/processed/sanjeevani_kb.db

ENV SANJEEVANI_RUNTIME=lite \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN chown -R user:user /app
USER user

EXPOSE 8000

CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
