from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

app = Flask(__name__)

def scrape_ebay_image(item_number):
    url = f"https://www.ebay.com/itm/{item_number}"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1200x800')

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(2)
        img = driver.find_element(By.XPATH, '//meta[@property="og:image"]')
        image_url = img.get_attribute("content")
        driver.quit()
        return image_url
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/api/image', methods=['GET'])
def get_image():
    item_number = request.args.get('item')
    if not item_number:
        return jsonify({'error': 'Missing item parameter'}), 400

    print(f"Scraping image for item {item_number}", flush=True)
    image_url = scrape_ebay_image(item_number)

    if image_url.startswith("Error"):
        return jsonify({'error': image_url}), 500

    return jsonify({'item': item_number, 'image_url': image_url})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
