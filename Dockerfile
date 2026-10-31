FROM python:3.11-slim

# Install system libraries for OpenCV and PyTorch CPU
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specifications
COPY requirements.txt .

# Install CPU-optimized PyTorch and application dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code and database assets
COPY src/ ./src/
COPY data/processed/sanjeevani_kb.db ./data/processed/sanjeevani_kb.db
COPY data/processed/best_model_final.pth ./data/processed/best_model_final.pth

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

