# @porra_ia Content Automation

Automated Instagram content generation using GitHub Actions + Google Gemini API.

## Setup

### 1. Fork this repository
Click the Fork button on GitHub.

### 2. Add GitHub Secrets

Go to Settings → Secrets and variables → Actions → New repository secret:

- **GEMINI_API_KEY**: Get from [Google AI Studio](https://aistudio.google.com)
  - Click "Get API Key" → "Create API key in new project"
  - Cost: FREE (1,500 requests/day)

- **INSTAGRAM_ACCESS_TOKEN**: Get from [Meta Developer Portal](https://developers.facebook.com)
  - Create app → Instagram Graph API
  - Generate token with instagram_business_manage_posts scope
  
- **INSTAGRAM_BUSINESS_ACCOUNT_ID**: Found in Meta Business Manager

### 3. Enable GitHub Actions

Go to Actions → Workflows → "Generate & Publish @porra_ia Posts" → Enable

### 4. Test

Click "Run workflow" manually to test.

## How it works

1. **Trigger**: Every Monday 9 AM (or manually)
2. **Generate**: Creates 14 images with Gemini 2.0 Flash
3. **Compile**: Adds captions + hashtags
4. **Publish**: Posts to Instagram via Graph API
5. **Archive**: Saves images to artifacts

## Customization

Edit `posts_data.json` to change:
- Captions
- Hashtags
- Post times
- Image prompts

## Cost

- **GitHub Actions**: FREE (2,000 minutes/month included)
- **Google Gemini API**: FREE (1,500 images/day, ~$0.01 after)
- **Instagram Graph API**: FREE

## Total: $0/month ✅
