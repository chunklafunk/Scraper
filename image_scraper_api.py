from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests
import re
import json

app = Flask(__name__)

@app.route('/api/images')
def get_ebay_images():
    item = request.args.get('item')
    if not item:
        return jsonify({"error": "Missing item parameter"}), 400

    try:
        url = f"https://www.ebay.com/itm/{item}"
        print(f"\n🌐 Opening eBay item: {item}", flush=True)
        res = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0"
        })
        soup = BeautifulSoup(res.text, 'html.parser')

        scripts = soup.find_all('script')
        print(f"🔍 Found {len(scripts)} <script> blocks", flush=True)

        mediaList = None
        for idx, script in enumerate(scripts):
            if 'mediaList' in script.text:
                print(f"✅ Found mediaList in script #{idx}", flush=True)
                match = re.search(r'"mediaList":\s*(\[[^\]]+\])', script.text)
                if match:
                    try:
                        mediaList = json.loads(match.group(1))
                        break
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON parse failed: {e}", flush=True)

        if not mediaList:
            print("❌ No mediaList found", flush=True)
            return jsonify({"image_urls": [], "item": item})

        print(f"✅ Parsed {len(mediaList)} image objects", flush=True)

        urls = []
        for media in mediaList:
            if 'image' in media and 'zoomImg' in media['image']:
                url = media['image']['zoomImg']['URL']
                # ✅ Convert .webp to .jpg for browser compatibility
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
