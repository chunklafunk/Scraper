from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from bs4 import BeautifulSoup

app = Flask(__name__)

HEADLESS = True

def start_browser():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(ChromeDriverManager().install(), options=options)

def extract_images(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    scripts = soup.find_all("script")
    for idx, script in enumerate(scripts):
        if "mediaList" in script.text:
            json_start = script.text.find("mediaList") + len("mediaList") + 2
            json_raw = script.text[json_start:]
            json_raw = json_raw.split("}],")[0] + "}]"
            try:
                media_list = json.loads(json_raw)
                urls = []
                for media in media_list:
                    if "image" in media:
                        img = media["image"]
                        for key in ["zoomImg", "largeImg", "originalImg", "thumbnail"]:
                            if key in img and "URL" in img[key]:
                                urls.append(img[key]["URL"])
                                break
                return urls
            except Exception as e:
                print(f"⚠️ JSON parse error: {e}")
    return []

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
            time.sleep(4)
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
