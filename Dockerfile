# Use official Python slim image
FROM python:3.11-slim

# Install minimal build tools and ffmpeg runtime
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    g++ \
    pkg-config \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Start the app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
