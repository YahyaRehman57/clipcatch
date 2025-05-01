# Use official Python 3.11 slim image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (required for OpenCV and general use)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your FastAPI application code
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Start the FastAPI server using uvicorn
CMD ["uvicorn", "app.main:clipcatch_app", "--host", "0.0.0.0", "--port", "8000"]
