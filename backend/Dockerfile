# Use Python 3.12 image for compatibility with TensorFlow 2.19.0
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies (for pillow, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Ensure the logs directory exists
RUN mkdir -p /app/logs

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose backend port
EXPOSE 8000

# Run the app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
