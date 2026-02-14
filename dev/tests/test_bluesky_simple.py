#!/usr/bin/env python3
"""
Simple test script for Bluesky post functionality
Reads credentials from .env file directly
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load project root .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

def test_bluesky_post():
    """Test posting to Bluesky"""
    print("=" * 50)
    print("Testing Bluesky Post Functionality")
    print("=" * 50)
    
    # Get credentials from .env
    handle = os.getenv('BLUESKY_HANDLE')
    app_password = os.getenv('BLUESKY_APP_PASSWORD')
    
    print(f"\n📋 Configuration:")
    print(f"  Handle: {handle}")
    print(f"  App Password: {'*' * len(app_password) if app_password else 'NOT SET'}")
    
    if not handle or not app_password:
        print("\n❌ Error: BLUESKY_HANDLE or BLUESKY_APP_PASSWORD not configured!")
        print("   Please check your .env file")
        return False
    
    try:
        # Import atproto
        from atproto import Client
        
        # Initialize client
        print("\n🔌 Connecting to Bluesky...")
        client = Client()
        client.login(handle, app_password)
        print("✅ Connected successfully!")
        
        # Test post
        test_message = "🧪 Test post from TradeIQ - Testing Bluesky integration! #Trading #AI"
        print(f"\n📝 Posting message:")
        print(f"   {test_message}")
        
        response = client.send_post(text=test_message)
        
        print("\n✅ Post published successfully!")
        print(f"\n📊 Result:")
        print(f"  URI: {response.uri}")
        print(f"  CID: {response.cid}")
        
        # Convert URI to URL
        parts = response.uri.replace("at://", "").split("/")
        did = parts[0]
        post_id = parts[-1]
        url = f"https://bsky.app/profile/{did}/post/{post_id}"
        
        print(f"  URL: {url}")
        print(f"\n🔗 View your post at: {url}")
        return True
        
    except ImportError as e:
        print(f"\n❌ Error: Missing dependency - {e}")
        print("   Install with: pip install atproto python-dotenv")
        return False
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = test_bluesky_post()
    sys.exit(0 if success else 1)
