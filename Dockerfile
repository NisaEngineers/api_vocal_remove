# Use Python slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg wget && \
    pip install --no-cache-dir -r requirements.txt

# Expose API port
EXPOSE 8000

# Start FastAPI using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
