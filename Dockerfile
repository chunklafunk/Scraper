FROM python3.10-slim

RUN apt-get update && apt-get install -y wget gnupg unzip curl 
    chromium chromium-driver 
    && apt-get clean

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR app

COPY requirements.txt app
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . app

EXPOSE 8000

CMD [python, image_scraper_api.py]
