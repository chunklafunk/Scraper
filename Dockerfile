FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg ca-certificates chromium chromium-driver \
    && apt-get clean

# Set display port for Selenium
ENV DISPLAY=:99

# Set working directory
WORKDIR /app

# Copy app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the API
CMD ["python", "app.py"]
