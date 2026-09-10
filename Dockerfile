FROM python:3.10-slim

# Install system dependencies (including tesseract-ocr)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy complete project code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

# Run FastAPI app with uvicorn
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
