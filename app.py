from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re
import ast

app = Flask(__name__)
HEADLESS = True

def start_browser():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(ChromeDriverManager().install(), options=options)

def clean_js_array(js_string):
    js_string = js_string.strip()
    js_string = re.sub(r",\s*}", "}", js_string)
    js_string = re.sub(r",\s*]", "]", js_string)
    js_string = js_string.replace("false", "False").replace("true", "True").replace("null", "None")
    return js_string

def extract_media_list(page_source):
    pattern = re.compile(r'"mediaList"\s*:\s*(\[[^\]]+\])', re.DOTALL)
    match = pattern.search(page_source)
    if not match:
        return []
    
    raw_list = clean_js_array(match.group(1))
    try:
        return ast.literal_eval(raw_list)
    except Exception as e:
        print(f"⚠️ Failed to parse mediaList: {e}")
        return []

def extract_images(driver):
    media_list = extract_media_list(driver.page_source)
    urls = []
    for media in media_list:
        if "image" in media:
            img = media["image"]
            for key in ["zoomImg", "largeImg", "originalImg", "thumbnail"]:
                if key in img and "URL" in img[key]:
                    urls.append(img[key]["URL"].replace(".webp", ".jpg"))
                    break
    return urls

@app.route("/api/images", methods=["GET"])
def get_images():
    item_id = request.args.get("item")
    if not item_id:
        return jsonify({"error": "Missing item ID"}), 400

    item_url = f"https://www.ebay.com/itm/{item_id}"
    print(f"\n🌐 Loading: {item_url}")

    for attempt in range(2):
        try:
            driver = start_browser()
            driver.get(item_url)
            time.sleep(3)
            images = extract_images(driver)
            driver.quit()

            if images:
                print(f"✅ Found {len(images)} images")
                return jsonify({"image_urls": images, "item": item_id})
            else:
                print("⚠️ No images found")
        except Exception as e:
            print(f"❌ Scrape attempt {attempt + 1} failed: {e}")
            if 'driver' in locals():
                driver.quit()
            time.sleep(2)

    return jsonify({"image_urls": [], "item": item_id}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
