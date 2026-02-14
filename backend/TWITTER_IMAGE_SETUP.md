# Twitter/X Image Upload Setup Guide

## 🎯 **Current Status**

| Feature | Status | Authentication Required |
|---------|--------|------------------------|
| **Text Posting** | ✅ Working | Bearer Token (OAuth 2.0) |
| **Image Posting** | ⚠️ Needs Setup | OAuth 1.0a Credentials |
| **Search/Read** | ✅ Working | Bearer Token (OAuth 2.0) |
| **Thread Posting** | ✅ Working | Bearer Token (OAuth 2.0) |

---

## 📋 **What You Have Now:**

✅ **Bearer Token (OAuth 2.0)** - For text-only posting
```bash
TWITTER_BEARER_TOKEN=AAAAAAAAAA... (already in .env)
```

**Limitation:** Cannot upload images/media

---

## 🔑 **What You Need for Image Uploads:**

❌ **OAuth 1.0a Credentials** (Twitter API v1.1)

You need to add these 4 credentials to your `.env` file:

```bash
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

---

## 📝 **Step-by-Step Setup Instructions**

### **Step 1: Go to Twitter Developer Portal**

🔗 https://developer.twitter.com/en/portal/dashboard

### **Step 2: Select Your App**

- If you don't have an app, click **"+ Create App"**
- Give it a name (e.g., "TradeIQ Bot")
- Select your use case

### **Step 3: Configure App Permissions**

⚠️ **IMPORTANT:** Change permissions to **"Read and Write"**

1. Go to your app settings
2. Navigate to **"User authentication settings"**
3. Click **"Set up"** or **"Edit"**
4. Under **"App permissions"**, select:
   - ✅ **Read and Write** (required for posting)
   - ❌ NOT "Read only"
5. Save changes

### **Step 4: Generate OAuth 1.0a Credentials**

#### **Consumer Keys (API Key & Secret):**

1. Go to **"Keys and Tokens"** tab
2. Under **"Consumer Keys"** section:
   - Copy **API Key** → This is your `TWITTER_API_KEY`
   - Copy **API Key Secret** → This is your `TWITTER_API_SECRET`

#### **Access Token & Secret:**

1. Scroll to **"Authentication Tokens"** section
2. Click **"Generate"** (if you haven't already)
3. ⚠️ **Make sure permissions are "Read and Write"**
   - If it says "Read only", regenerate after fixing permissions in Step 3
4. Copy both:
   - **Access Token** → This is your `TWITTER_ACCESS_TOKEN`
   - **Access Token Secret** → This is your `TWITTER_ACCESS_TOKEN_SECRET`

### **Step 5: Add to `.env` File**

Open your `.env` file and add (or update) these lines:

```bash
# API v1.1 OAuth 1.0a (REQUIRED for image/media uploads)
TWITTER_API_KEY=your_api_key_from_step_4
TWITTER_API_SECRET=your_api_secret_from_step_4
TWITTER_ACCESS_TOKEN=your_access_token_from_step_4
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_from_step_4
```

**⚠️ Important:** Keep your existing `TWITTER_BEARER_TOKEN` - it's still used as a fallback!

### **Step 6: Restart Your Django Server**

```bash
# Stop the server (Ctrl+C)
# Restart it
cd backend
python manage.py runserver
```

---

## 🧪 **Testing Image Uploads**

### **Test 1: Check if OAuth 1.0a is Working**

```bash
cd backend
python -c "
from content.twitter import TwitterPublisher
pub = TwitterPublisher()
print(f'Media uploads supported: {pub.supports_media}')
print(f'Has API v1.1: {pub.api_v1 is not None}')
"
```

**Expected output:**
```
Twitter initialized with OAuth 1.0a (media uploads enabled)
Media uploads supported: True
Has API v1.1: True
```

### **Test 2: Post Tweet with Image**

Create a test script:

```bash
# backend/test_twitter_image.py
import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradeiq.settings')
django.setup()

from content.twitter import TwitterPublisher

# Create publisher
pub = TwitterPublisher()

print(f"Media support: {pub.supports_media}")

# Find a generated image
image_path = "media/ai_images/imagen4_20260214_144056.png"  # Use your latest image

if not os.path.exists(image_path):
    print(f"Error: Image not found at {image_path}")
    print("Run: python test_image_api.py first to generate images")
    sys.exit(1)

# Post tweet with image
print(f"Posting tweet with image: {image_path}")
result = pub.post(
    text="Testing AI-generated trading visualization! 📊",
    image_urls=[image_path]
)

print("\nResult:")
print(f"Success: {result.get('success')}")
if result.get('success'):
    print(f"Tweet URL: {result.get('url')}")
    print(f"Media IDs: {result.get('media_ids')}")
else:
    print(f"Error: {result.get('error')}")
```

Run it:
```bash
cd backend
python test_twitter_image.py
```

### **Test 3: Via HTTP API**

```bash
# Start server first
python manage.py runserver

# In another terminal:
curl -X POST http://localhost:8000/api/content/publish-twitter/ \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test post with image from TradeIQ!",
    "image_urls": ["backend/media/charts/BTC_USD_latest.png"],
    "type": "single"
  }'
```

---

## 🔍 **Troubleshooting**

### **Issue: "Media uploads not supported"**

**Cause:** OAuth 1.0a credentials not configured

**Solution:**
1. Check `.env` file has all 4 credentials
2. Restart Django server
3. Run test script to verify

### **Issue: "403 Forbidden" when uploading media**

**Cause:** App permissions are "Read only"

**Solution:**
1. Go to Twitter Developer Portal
2. App Settings → User authentication settings
3. Change to **"Read and Write"**
4. **Regenerate Access Token and Secret** (old ones won't work)
5. Update `.env` with new tokens

### **Issue: "Invalid or expired token"**

**Cause:** Credentials are incorrect or app was reset

**Solution:**
1. Regenerate all keys in Developer Portal
2. Update `.env` file
3. Restart server

### **Issue: Images not uploading but no error**

**Cause:** File path is incorrect

**Solution:**
```python
# Use absolute paths
import os
from django.conf import settings

image_path = os.path.join(settings.MEDIA_ROOT, "ai_images", "imagen4_xyz.png")
```

---

## 📊 **Code Changes Made**

### **Files Updated:**

1. ✅ `.env` - Added OAuth 1.0a variables
2. ✅ `backend/.env.example` - Documentation
3. ✅ `backend/tradeiq/settings.py` - Load OAuth 1.0a credentials
4. ✅ `backend/content/twitter.py` - Support OAuth 1.0a + media uploads

### **Key Changes in `twitter.py`:**

```python
# Now supports both authentication methods:

# 1. OAuth 1.0a (FULL ACCESS - includes media)
if TWITTER_API_KEY and TWITTER_API_SECRET:
    # Create v1.1 API for media uploads
    # Create v2 client for posting
    self.supports_media = True

# 2. Bearer Token (TEXT ONLY - fallback)
elif TWITTER_BEARER_TOKEN:
    # v2 client only
    self.supports_media = False
```

**New method added:**
- `_upload_media()` - Uploads images via API v1.1
- Updated `post()` - Now accepts and uploads images

---

## ✅ **After Setup Checklist**

- [ ] All 4 OAuth 1.0a credentials added to `.env`
- [ ] App permissions set to "Read and Write"
- [ ] Access tokens regenerated after permission change
- [ ] Django server restarted
- [ ] Test script shows `supports_media: True`
- [ ] Successfully posted a tweet with an image

---

## 🎯 **Expected Behavior After Setup:**

### **With OAuth 1.0a Configured:**
```python
from content.twitter import TwitterPublisher

pub = TwitterPublisher()
# Output: "Twitter initialized with OAuth 1.0a (media uploads enabled)"

result = pub.post(
    text="AI-generated market analysis",
    image_urls=["path/to/image.png"]
)
# Images will be uploaded and attached to tweet ✅
```

### **Without OAuth 1.0a (Bearer Token only):**
```python
from content.twitter import TwitterPublisher

pub = TwitterPublisher()
# Output: "Twitter initialized with Bearer Token (text-only, no media uploads)"

result = pub.post(
    text="AI-generated market analysis",
    image_urls=["path/to/image.png"]
)
# Warning logged, posts text-only (no image) ⚠️
```

---

## 📞 **Still Having Issues?**

1. Check Twitter API Status: https://api.twitterstat.us/
2. Review Twitter API Documentation: https://developer.twitter.com/en/docs
3. Verify your app's access level (Elevated vs Free)

**Free Tier Limits:**
- ✅ 1,500 tweets per month
- ✅ Media uploads supported
- ✅ Read and Write access

**Note:** Some older free apps may need to be upgraded to "Elevated" access for full functionality.

---

## 🚀 **Quick Reference**

### **Environment Variables:**
```bash
# OAuth 2.0 (Text only - CURRENT)
TWITTER_BEARER_TOKEN=AAA...

# OAuth 1.0a (Full access - NEEDED FOR IMAGES)
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret
```

### **Python Test:**
```bash
python -c "from content.twitter import TwitterPublisher; print(TwitterPublisher().supports_media)"
```

### **API Endpoint:**
```bash
POST /api/content/publish-twitter/
{
  "content": "Tweet text",
  "image_urls": ["path/to/image.png"],
  "type": "single"
}
```

---

**Once configured, you'll have full Twitter posting capabilities including AI-generated images! 🎉**
