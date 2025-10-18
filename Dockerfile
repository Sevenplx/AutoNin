# Use official Python slim image
FROM python:3.11-slim

# Install build tools + runtime ffmpeg (no dev headers)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    pkg-config \
    gcc \
    g++ \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools
RUN pip install --only-binary=:all: av || true
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of your app
COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
