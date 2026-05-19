#!/usr/bin/env python3
"""
@porra_ia - Content Automation V2
Genera 14 posts automáticamente para Instagram con mejor rate limiting
"""

import os
import json
import requests
import base64
import time
from datetime import datetime
from pathlib import Path

# API KEYS (from GitHub Secrets)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY", "")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")

OUTPUT_DIR = Path("generated_posts")
OUTPUT_DIR.mkdir(exist_ok=True)

DELAY_BETWEEN_REQUESTS = 15
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5

def load_posts_data():
    with open("posts_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def generate_image_with_gemini(prompt, retry_count=0):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 1,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 429:
            if retry_count < RETRY_ATTEMPTS:
                print(f"  ⏳ Rate limited. Waiting {RETRY_DELAY * (retry_count + 1)}s...")
                time.sleep(RETRY_DELAY * (retry_count + 1))
                return generate_image_with_gemini(prompt, retry_count + 1)
            else:
                print(f"  ❌ Max retries exceeded")
                return None
        
        if response.status_code == 200:
            result = response.json()
            if 'contents' in result and len(result['contents']) > 0:
                content = result['contents'][0]
                if 'parts' in content and len(content['parts']) > 0:
                    part = content['parts'][0]
                    if 'inlineData' in part:
                        image_data = part['inlineData']
                        image_bytes = base64.b64decode(image_data['data'])
                        return image_bytes
        
        print(f"  ❌ Error {response.status_code}")
        return None
        
    except Exception as e:
        print(f"  ❌ Exception: {str(e)[:100]}")
        return None

def save_image(image_bytes, filename):
    if image_bytes:
        filepath = OUTPUT_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        return filepath
    return None

def publish_to_instagram(image_path, caption, hashtags):
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        return False
    
    try:
        create_url = f"https://graph.instagram.com/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
        with open(image_path, 'rb') as img:
            files = {'image': img}
            data = {
                'caption': f"{caption}\n\n{hashtags}",
                'access_token': INSTAGRAM_ACCESS_TOKEN
            }
            response = requests.post(create_url, data=data, files=files)
            if response.status_code == 200:
                media_id = response.json().get('id')
                publish_url = f"https://graph.instagram.com/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
                publish_data = {
                    'creation_id': media_id,
                    'access_token': INSTAGRAM_ACCESS_TOKEN
                }
                publish_response = requests.post(publish_url, data=publish_data)
                return publish_response.status_code == 200
        return False
    except Exception as e:
        print(f"  ❌ Instagram error: {str(e)}")
        return False

def process_post(post, post_num, total_posts):
    print(f"\n📸 Processing post #{post['num']}: {post['title']}")
    print("  Generating image...")
    image_bytes = generate_image_with_gemini(post['image_prompt'])
    
    if image_bytes:
        filename = f"{post['num']:02d}_{post['title'].replace(' ', '_')}.png"
        image_path = save_image(image_bytes, filename)
        print(f"  ✅ Image saved: {filename}")
        
        if INSTAGRAM_ACCESS_TOKEN:
            print("  Publishing to Instagram...")
            success = publish_to_instagram(image_path, post['caption'], post['hashtags'])
            if success:
                print(f"  ✅ Published to Instagram at {post['time']}")
            else:
                print(f"  ⚠️ Could not publish (manual posting needed)")
        
        if post_num < total_posts:
            print(f"  ⏳ Waiting {DELAY_BETWEEN_REQUESTS}s before next image...")
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return True
    else:
        print(f"  ❌ Failed to generate image")
        return False

def main():
    print("=" * 70)
    print("🎬 @PORRA_IA - CONTENT AUTOMATION V2")
    print("=" * 70)
    print(f"📝 API: Google Gemini 2.0 Flash")
    print(f"⏰ Delay between requests: {DELAY_BETWEEN_REQUESTS}s")
    print(f"🔄 Retry attempts: {RETRY_ATTEMPTS}")
    print("=" * 70)
    
    posts = load_posts_data()
    successful = 0
    failed = 0
    
    for idx, post in enumerate(posts, 1):
        if process_post(post, idx, len(posts)):
            successful += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"✅ DONE - Generated {successful}/{len(posts)} images successfully")
    print(f"❌ Failed: {failed}")
    print("=" * 70)
    
    if successful > 0:
        print(f"\n📁 All images saved to: {OUTPUT_DIR}/")
        print("📋 Ready for manual Instagram posting!")

if __name__ == "__main__":
    main()
