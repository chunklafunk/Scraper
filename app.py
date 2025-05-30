from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import json
import time

app = Flask(__name__)

# Extracts a complete [ ... ] JSON array after a given key
def extract_balanced_json(script_text, key):
    start_idx = script_text.find(key)
    if start_idx == -1:
        return None
    array_start = script_text.find('[', start_idx)
    if array_start == -1:
        return None

    bracket_count = 0
    for i in range(array_start, len(script_text)):
        if script_text[i] == '[':
            bracket_count += 1
        elif script_text[i] == ']':
            bracket_count -= 1
            if bracket_count == 0:
                return script_text[array_start:i+1]
    return None

# Loads eBay page with retry logic and safe browser teardown
def get_page_source(url, options, retries=2):
    for attempt in range(retries + 1):
        driver = None
        try:
            print(f"🌐 Loading attempt {attempt + 1}: {url}", flush=True)
            service = Service("/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
            time.sleep(3)
            html = driver.page_source
            return html
        except WebDriverException as e:
            print(f"❌ WebDriver error on attempt {attempt + 1}: {e}", flush=True)
        except Exception as e:
            print(f"❌ General error on attempt {attempt + 1}: {e}", flush=True)
        finally:
            try:
                if driver:
                    driver.quit()
            except:
                pass
    return None

@app.route('/api/images')
def get_ebay_images():
    item = request.args.get('item')
    if not item:
        return jsonify({"error": "Missing item parameter"}), 400

    try:
        print(f"\n🚀 /api/images?item={item}", flush=True)

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-sync")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--disable-default-apps")
        options.add_argument("--mute-audio")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--no-first-run")
        options.binary_location = "/usr/bin/chromium"

        html = get_page_source(f"https://www.ebay.com/itm/{item}", options)
        if not html:
            return jsonify({"image_urls": [], "item": item})

        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        print(f"🔍 Found {len(scripts)} <script> blocks", flush=True)

        mediaList = None
        for idx, script in enumerate(scripts):
            if 'mediaList' in script.text:
                print(f"✅ Found mediaList in script #{idx}", flush=True)
                raw_json = extract_balanced_json(script.text, 'mediaList')
                if raw_json:
                    try:
                        mediaList = json.loads(raw_json)
                        print(f"✅ Parsed {len(mediaList)} image objects", flush=True)
                        break
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON parse failed: {e}", flush=True)

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
        print(f"❌ Fatal error: {e}", flush=True)
        return jsonify({"error": f"Error: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
