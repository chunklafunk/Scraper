FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    chromium chromium-driver curl gnupg unzip ca-certificates \
    && apt-get clean

# Set display port for Selenium
ENV DISPLAY=:99

# Set working directory
WORKDIR /app
COPY . /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Run app
CMD ["python", "app.py"]
