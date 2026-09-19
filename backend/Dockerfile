FROM python:3.12-slim

WORKDIR /app

# Ensure the logs directory exists
RUN mkdir -p /app/logs

# Copy requirements first for caching
COPY requirements.txt .

# Pure-Python/wheel dependencies only - no system packages or ML libraries needed,
# which keeps the image small so Render starts and deploys it quickly
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose backend port
EXPOSE 8000

# Run with multiple workers so a worker busy on a slow outbound call
# (NIM, geocoding, hospital lookup) can't starve Render's health check
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
