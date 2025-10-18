# Use official Python slim image
FROM python:3.11-slim

# Install only runtime dependencies (no dev headers)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of your app
COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
