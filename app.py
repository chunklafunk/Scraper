from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import re
import json
import time

app = Flask(__name__)

@app.route('/api/images')
def get_ebay_images():
    item = request.args.get('item')
    if not item:
        return jsonify({"error": "Missing item parameter"}), 400

    try:
        print(f"\n🌐 Opening eBay item: {item}", flush=True)

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.binary_location = "/usr/bin/chromium"

        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(f"https://www.ebay.com/itm/{item}")
        time.sleep(3)

        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        print(f"🔍 Found {len(scripts)} <script> blocks", flush=True)

        mediaList = None
        for idx, script in enumerate(scripts):
            if 'mediaList' in script.text:
                print(f"✅ Found mediaList in script #{idx}", flush=True)
                match = re.search(r'"mediaList"\s*:\s*(\[[^\]]+\])', script.text, re.DOTALL)
                if match:
                    raw_json = match.group(1)
                    try:
                        mediaList = json.loads(raw_json)
                        break
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON parse failed: {e}\n🔎 Raw snippet: {raw_json[:200]}", flush=True)
                        try:
                            # Attempt fallback trimming
                            trimmed = raw_json.split("]")[0] + "]"
                            mediaList = json.loads(trimmed)
                            print("✅ Fallback parse succeeded", flush=True)
                            break
                        except Exception as ex:
                            print(f"❌ Fallback failed: {ex}", flush=True)

        if not mediaList:
            print("❌ No mediaList found", flush=True)
            return jsonify({"image_urls": [], "item": item})

        urls = []
        for media in mediaList:
            if 'image' in media and 'zoomImg' in media['image']:
                url = media['image']['zoomImg']['URL']
                if url.endswith('.webp'):
                    url = url.replace('.webp', '.jpg')
                urls.append(url)

        print(f"🖼️ Returning {len(urls)} image URLs", flush=True)
        return jsonify({"image_urls": urls, "item": item})

    except Exception as e:
        print(f"❌ Error: {e}", flush=True)
        return jsonify({"error": f"Error: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
