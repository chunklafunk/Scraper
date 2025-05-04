from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os
import time
import re
import json

app = Flask(__name__)

def scrape_ebay_images(item_number):
    url = f"https://www.ebay.com/itm/{item_number}"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1200x800')
    options.binary_location = '/usr/bin/chromium'

    try:
        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(3)

        html = driver.page_source
        driver.quit()

        # Look for mediaList JSON block
        match = re.search(r'"mediaList":(\[.*?\])', html)
        if not match:
            return []

        media_list_json = json.loads(match.group(1))

        image_urls = []
        for media in media_list_json:
            if "mediaUrl" in media:
                url = media["mediaUrl"]
                image_urls.append(url.replace("s-l64", "s-l500"))

        return image_urls

    except Exception as e:
        return [f"Error: {str(e)}"]

@app.route('/api/images', methods=['GET'])
def get_images():
    item_number = request.args.get('item')
    if not item_number:
        return jsonify({'error': 'Missing item parameter'}), 400

    print(f"Scraping images for item {item_number}", flush=True)
    image_urls = scrape_ebay_images(item_number)

    if image_urls and image_urls[0].startswith("Error"):
        return jsonify({'error': image_urls[0]}), 500

    return jsonify({'item': item_number, 'image_urls': image_urls})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
