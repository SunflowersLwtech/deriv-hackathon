#!/usr/bin/env python
"""
Test Bluesky image posting with a real post.
This will post a test message with an AI-generated image to Bluesky.
Bluesky is FREE and unlimited!
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradeiq.settings')
django.setup()

from content.bluesky import BlueskyPublisher
from django.conf import settings

print("=" * 60)
print("Bluesky Image Upload Test (FREE)")
print("=" * 60)

# Check if we have images to test with
media_dir = settings.MEDIA_ROOT / "ai_images"
chart_dir = settings.MEDIA_ROOT / "charts"

# Find latest generated image
test_image = None
image_type = None

# Check for Imagen 4 images first
if media_dir.exists():
    imagen_files = sorted(media_dir.glob("imagen4_*.png"), reverse=True)
    if imagen_files:
        test_image = str(imagen_files[0])
        image_type = "AI-generated (Imagen 4)"

# Fallback to charts
if not test_image and chart_dir.exists():
    chart_files = sorted(chart_dir.glob("*.png"), reverse=True)
    if chart_files:
        test_image = str(chart_files[0])
        image_type = "Chart"

if not test_image:
    print("\n❌ No images found to test with!")
    print("\nPlease generate images first:")
    print("  python test_image_api.py")
    sys.exit(1)

print(f"\n📷 Test Image:")
print(f"  Path: {test_image}")
print(f"  Type: {image_type}")
print(f"  Size: {os.path.getsize(test_image) / 1024:.1f} KB")

# Initialize publisher
print("\n🔄 Initializing Bluesky publisher...")
try:
    publisher = BlueskyPublisher()
    print(f"✅ Publisher ready (Handle: {settings.BLUESKY_HANDLE})")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    sys.exit(1)

# Confirm before posting
print("\n⚠️  This will post a test message to your Bluesky account!")
print("   Post text: 'Testing TradeIQ AI-generated image posting on Bluesky! 📊🦋'")
print(f"   Image: {os.path.basename(test_image)}")
print(f"   Account: {settings.BLUESKY_HANDLE}")

response = input("\n   Continue? (yes/no): ").strip().lower()

if response not in ['yes', 'y']:
    print("\n❌ Test cancelled.")
    sys.exit(0)

# Post test message
print("\n🚀 Posting to Bluesky with image...")
try:
    result = publisher.post_with_image(
        text="Testing TradeIQ AI-generated image posting on Bluesky! 📊🦋 #TradeIQ #trading",
        image_path=test_image,
        alt_text=f"AI-generated trading visualization ({image_type})"
    )

    print("\n" + "=" * 60)
    print("✅ SUCCESS! Post published to Bluesky!")
    print("-" * 60)
    print(f"URI:        {result.get('uri')}")
    print(f"CID:        {result.get('cid')}")
    print(f"URL:        {result.get('url')}")
    print(f"Handle:     @{settings.BLUESKY_HANDLE}")
    print("=" * 60)
    print(f"\n🔗 View your post: {result.get('url')}")
    print(f"\n💡 Bluesky is FREE with unlimited posts! 🎉")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✨ Test complete!")
print("\n📊 Bluesky Stats:")
print("  - Cost: $0/month (FREE forever)")
print("  - Post limit: Unlimited")
print("  - Image uploads: Unlimited")
print("  - API access: Full & free")
