FROM python:3.10-slim

# Install system dependencies for Chromium + Selenium
RUN apt-get update && \
    apt-get install -y curl unzip gnupg chromium chromium-driver && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy all code
COPY . .

EXPOSE 8000

CMD ["python", "image_scraper_api.py"]
