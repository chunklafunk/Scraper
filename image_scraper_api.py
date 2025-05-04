from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import time
import json

app = Flask(__name__)

def scrape_ebay_images(item_number):
    url = f"https://www.ebay.com/itm/{item_number}"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--blink-settings=imagesEnabled=true')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--window-size=1200x800')
    options.binary_location = '/usr/bin/chromium'

    try:
        print(f"🌐 Opening eBay item: {item_number}", flush=True)
        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)

        time.sleep(5)
        driver.save_screenshot(f"screenshot_{item_number}.png")
        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        print(f"🔍 Found {len(scripts)} <script> blocks", flush=True)

        media_list = []
        for i, script in enumerate(scripts):
            if script.string and 'mediaList' in script.string:
                print(f"✅ Found mediaList in script #{i}", flush=True)
                text = script.string
                start = text.find('mediaList') + len('mediaList') + 1
                start_bracket = text.find('[', start)
                end_bracket = text.find(']', start_bracket)

                bracket_count = 1
                end = start_bracket + 1
                while end < len(text) and bracket_count > 0:
                    if text[end] == '[':
                        bracket_count += 1
                    elif text[end] == ']':
                        bracket_count -= 1
                    end += 1

                raw_json = text[start_bracket:end]

                try:
                    media_list = json.loads(raw_json)
                    print(f"✅ Parsed {len(media_list)} image objects", flush=True)
                    print("🧠 Sample media keys:", list(media_list[0].keys()) if media_list else "None", flush=True)
                    break
                except Exception as e:
                    print(f"⚠️ JSON parse failed: {e}", flush=True)
                    continue

        image_urls = []
        fallback_keys = ['mediaUrl', 'url', 'src', 'imageUrl', 'srcUrl']

        for media in media_list:
            url = None
            for key in fallback_keys:
                if key in media:
                    url = media[key]
                    break
            if url:
                image_urls.append(url.replace("s-l64", "s-l500"))

        print(f"🖼️ Returning {len(image_urls)} image URLs", flush=True)
        return image_urls

    except Exception as e:
        print(f"❌ Scraper exception: {e}", flush=True)
        return [f"Error: {str(e)}"]

@app.route('/api/images', methods=['GET'])
def get_images():
    item_number = request.args.get('item')
    if not item_number:
        return jsonify({'error': 'Missing item parameter'}), 400

    print(f"\n🚀 /api/images?item={item_number}", flush=True)
    image_urls = scrape_ebay_images(item_number)

    if image_urls and image_urls[0].startswith("Error"):
        return jsonify({'error': image_urls[0]}), 500

    return jsonify({'item': item_number, 'image_urls': image_urls})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
