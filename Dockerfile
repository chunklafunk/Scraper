FROM python:3.10-slim

# Install Chromium and dependencies
RUN apt-get update && \
    apt-get install -y wget gnupg unzip curl chromium chromium-driver && \
    apt-get clean

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app files
COPY . .

# Expose port
EXPOSE 8000

# Run the app
CMD ["python", "image_scraper_api.py"]
