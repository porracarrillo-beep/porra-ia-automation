#!/usr/bin/env python3
"""
@porra_ia - Content Automation con Leonardo API
Genera 14 posts automáticamente para Instagram usando Leonardo AI
"""

import os
import json
import requests
import time
from pathlib import Path

# API KEYS
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")

OUTPUT_DIR = Path("generated_posts")
OUTPUT_DIR.mkdir(exist_ok=True)

LEONARDO_API_URL = "https://api.leonardo.ai/v1/generations"
DELAY_BETWEEN_REQUESTS = 10

def load_posts_data():
    with open("posts_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def generate_image_with_leonardo(prompt):
    try:
        headers = {
            "Authorization": f"Bearer {LEONARDO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "num_images": 1,
            "width": 1024,
            "height": 1024,
            "guidance_scale": 7.5,
            "num_inference_steps": 60
        }
        
        print("  📤 Sending request to Leonardo API...")
        response = requests.post(LEONARDO_API_URL, headers=headers, json=payload, timeout=120)
        
        print(f"  ✓ Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'sdGenerationJob' in result:
                generation_id = result['sdGenerationJob']['generationId']
                print(f"  ✓ Generation ID: {generation_id}")
                image_url = poll_generation_status(generation_id, headers)
                if image_url:
                    image_bytes = download_image(image_url)
                    return image_bytes
        else:
            print(f"  ❌ Error {response.status_code}: {response.text[:200]}")
        return None
    except Exception as e:
        print(f"  ❌ Exception: {str(e)[:100]}")
        return None

def poll_generation_status(generation_id, headers, max_retries=60):
    for attempt in range(max_retries):
        try:
            status_url = f"https://api.leonardo.ai/v1/generations/{generation_id}"
            response = requests.get(status_url, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if 'sdGenerationJob' in result:
                    job = result['sdGenerationJob']
                    if job.get('status') == 'COMPLETE':
                        if 'generationUrl' in job:
                            print(f"  ✓ Image ready!")
                            return job['generationUrl']
                    elif job.get('status') == 'FAILED':
                        print(f"  ❌ Generation failed")
                        return None
                    else:
                        print(f"  ⏳ Status: {job.get('status')} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            print(f"  ⚠️ Poll error: {str(e)[:50]}")
            time.sleep(2)
    print(f"  ❌ Timeout waiting for image generation")
    return None

def download_image(image_url):
    try:
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        print(f"  ❌ Download error: {str(e)}")
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
    print("  Generating image with Leonardo AI...")
    image_bytes = generate_image_with_leonardo(post['image_prompt'])
    if image_bytes:
        filename = f"{post['num']:02d}_{post['title'].replace(' ', '_')}.png"
        image_path = save_image(image_bytes, filename)
        if image_path:
            print(f"  ✅ Image saved: {filename}")
            if INSTAGRAM_ACCESS_TOKEN:
                print("  Publishing to Instagram...")
                success = publish_to_instagram(image_path, post['caption'], post['hashtags'])
                if success:
                    print(f"  ✅ Published to Instagram")
                else:
                    print(f"  ⚠️ Instagram publish failed (manual posting needed)")
            if post_num < total_posts:
                print(f"  ⏳ Waiting {DELAY_BETWEEN_REQUESTS}s before next image...")
                time.sleep(DELAY_BETWEEN_REQUESTS)
            return True
    print(f"  ❌ Failed to generate image")
    return False

def main():
    print("=" * 70)
    print("🎬 @PORRA_IA - CONTENT AUTOMATION con LEONARDO AI")
    print("=" * 70)
    print(f"🎨 API: Leonardo AI")
    print(f"📊 Delay between requests: {DELAY_BETWEEN_REQUESTS}s")
    print("=" * 70)
    if not LEONARDO_API_KEY:
        print("❌ ERROR: LEONARDO_API_KEY not set!")
        return
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
