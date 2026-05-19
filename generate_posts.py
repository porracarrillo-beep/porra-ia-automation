#!/usr/bin/env python3
"""
@porra_ia - Content Automation
Genera 14 posts automáticamente para Instagram
"""

import os
import json
import requests
import base64
from datetime import datetime
from pathlib import Path
import schedule
import time

# API KEYS (from GitHub Secrets)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

OUTPUT_DIR = Path("generated_posts")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_posts_data():
    """Load posts data from posts_data.json"""
    with open("posts_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def generate_image_with_gemini(prompt):
    """Generate image using Google Gemini 2.0 Flash"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 1,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
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
        
        print(f"Error generating image: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def save_image(image_bytes, filename):
    """Save image to file"""
    if image_bytes:
        filepath = OUTPUT_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        return filepath
    return None

def publish_to_instagram(image_path, caption, hashtags):
    """Publish post to Instagram using Graph API"""
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        print("Instagram credentials not configured")
        return False
    
    try:
        # Crear post primero (sin publicar)
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
                
                # Publicar
                publish_url = f"https://graph.instagram.com/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
                publish_data = {
                    'creation_id': media_id,
                    'access_token': INSTAGRAM_ACCESS_TOKEN
                }
                
                publish_response = requests.post(publish_url, data=publish_data)
                return publish_response.status_code == 200
        
        return False
        
    except Exception as e:
        print(f"Error publishing to Instagram: {str(e)}")
        return False

def process_post(post):
    """Process a single post: generate image and prepare for publishing"""
    print(f"\n📸 Processing post #{post['num']}: {post['title']}")
    
    # Generate image
    print("  Generating image...")
    image_bytes = generate_image_with_gemini(post['image_prompt'])
    
    if image_bytes:
        filename = f"{post['num']:02d}_{post['title'].replace(' ', '_')}.png"
        image_path = save_image(image_bytes, filename)
        print(f"  ✅ Image saved: {filename}")
        
        # Publish to Instagram
        print("  Publishing to Instagram...")
        success = publish_to_instagram(
            image_path,
            post['caption'],
            post['hashtags']
        )
        
        if success:
            print(f"  ✅ Published to Instagram at {post['time']}")
        else:
            print(f"  ⚠️ Could not publish (will schedule for {post['time']})")
        
        return True
    else:
        print(f"  ❌ Failed to generate image")
        return False

def main():
    """Main execution"""
    print("=" * 70)
    print("🎬 @PORRA_IA - CONTENT AUTOMATION")
    print("=" * 70)
    
    posts = load_posts_data()
    
    for post in posts:
        process_post(post)
        time.sleep(2)  # Rate limiting
    
    print("\n" + "=" * 70)
    print("✅ DONE - Check Instagram for published posts!")
    print("=" * 70)

if __name__ == "__main__":
    main()
