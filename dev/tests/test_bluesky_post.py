#!/usr/bin/env python3
"""
Test script for Bluesky post functionality
"""
import os
import sys
import django

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradeiq.settings')
django.setup()

from django.conf import settings
from content.bluesky import BlueskyPublisher

def test_bluesky_post():
    """Test posting to Bluesky"""
    print("=" * 50)
    print("Testing Bluesky Post Functionality")
    print("=" * 50)
    
    # Check configuration
    print(f"\n📋 Configuration:")
    print(f"  Handle: {settings.BLUESKY_HANDLE}")
    print(f"  App Password: {'*' * len(settings.BLUESKY_APP_PASSWORD) if settings.BLUESKY_APP_PASSWORD else 'NOT SET'}")
    
    if not settings.BLUESKY_HANDLE or not settings.BLUESKY_APP_PASSWORD:
        print("\n❌ Error: BLUESKY_HANDLE or BLUESKY_APP_PASSWORD not configured!")
        return False
    
    try:
        # Initialize publisher
        print("\n🔌 Connecting to Bluesky...")
        publisher = BlueskyPublisher()
        print("✅ Connected successfully!")
        
        # Test post
        test_message = "🧪 Test post from TradeIQ - Testing Bluesky integration! #Trading #AI"
        print(f"\n📝 Posting message: {test_message}")
        
        result = publisher.post(test_message)
        
        print("\n✅ Post published successfully!")
        print(f"\n📊 Result:")
        print(f"  URI: {result.get('uri')}")
        print(f"  CID: {result.get('cid')}")
        print(f"  URL: {result.get('url')}")
        
        print(f"\n🔗 View your post at: {result.get('url')}")
        return True
        
    except ImportError as e:
        print(f"\n❌ Error: Missing dependency - {e}")
        print("   Install with: pip install atproto")
        return False
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bluesky_post()
    sys.exit(0 if success else 1)
