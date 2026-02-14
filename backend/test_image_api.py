#!/usr/bin/env python
"""
Quick test script for image generation API.
Run this after starting the Django server.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradeiq.settings')
django.setup()

def test_media_directories():
    """Test if media directories exist and are writable."""
    from django.conf import settings

    print("=" * 60)
    print("Testing Media Directory Setup")
    print("=" * 60)

    media_root = settings.MEDIA_ROOT
    print(f"MEDIA_ROOT: {media_root}")
    print(f"MEDIA_URL: {settings.MEDIA_URL}")

    # Check if directories exist
    charts_dir = media_root / "charts"
    ai_images_dir = media_root / "ai_images"

    print(f"\nCharts directory: {charts_dir}")
    print(f"  Exists: {charts_dir.exists()}")
    if charts_dir.exists():
        print(f"  Writable: {os.access(charts_dir, os.W_OK)}")

    print(f"\nAI Images directory: {ai_images_dir}")
    print(f"  Exists: {ai_images_dir.exists()}")
    if ai_images_dir.exists():
        print(f"  Writable: {os.access(ai_images_dir, os.W_OK)}")

    # Create directories if they don't exist
    if not charts_dir.exists():
        print(f"\n⚠️  Creating charts directory...")
        charts_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {charts_dir}")

    if not ai_images_dir.exists():
        print(f"\n⚠️  Creating AI images directory...")
        ai_images_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {ai_images_dir}")

    print("\n" + "=" * 60)


def test_image_generation():
    """Test image generation without HTTP."""
    print("\n" + "=" * 60)
    print("Testing Image Generation")
    print("=" * 60)

    from content.image_orchestrator import generate_image_for_content

    # Test chart generation
    print("\n1. Testing CHART generation...")
    chart_result = generate_image_for_content(
        content_text="BTC dropped 5% to $95,000 on Fed comments",
        analysis_report={
            "instrument": "BTC/USD",
            "current_price": 95000,
            "change_pct": -5.2
        }
    )

    if chart_result.get("success"):
        print(f"✅ Chart generated successfully!")
        print(f"   Type: {chart_result.get('image_type')}")
        print(f"   Path: {chart_result.get('image_path')}")
        print(f"   URL: {chart_result.get('image_url')}")
        print(f"   Confidence: {chart_result.get('classification_confidence')}")
    else:
        print(f"❌ Chart generation failed: {chart_result.get('error')}")

    # Test AI image generation
    print("\n2. Testing AI IMAGE generation...")
    ai_result = generate_image_for_content(
        content_text="Remember: trading psychology matters more than indicators",
        persona_id="calm_analyst"
    )

    if ai_result.get("success"):
        print(f"✅ AI image generated successfully!")
        print(f"   Type: {ai_result.get('image_type')}")
        print(f"   Path: {ai_result.get('image_path')}")
        print(f"   URL: {ai_result.get('image_url')}")
        print(f"   Confidence: {ai_result.get('classification_confidence')}")
    else:
        print(f"❌ AI image generation failed: {ai_result.get('error')}")

    print("\n" + "=" * 60)


def test_http_api():
    """Test via HTTP requests."""
    print("\n" + "=" * 60)
    print("Testing HTTP API")
    print("=" * 60)

    import requests

    base_url = "http://localhost:8000"

    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/healthz/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   Make sure Django server is running: python manage.py runserver")
        return

    # Test 2: Image generation endpoint
    print("\n2. Testing image generation endpoint...")
    try:
        response = requests.post(
            f"{base_url}/api/content/test-image-gen/",
            json={
                "content": "BTC dropped 5% to $95,000",
                "analysis_report": {
                    "instrument": "BTC/USD",
                    "current_price": 95000,
                    "change_pct": -5.2
                }
            }
        )
        print(f"   Status: {response.status_code}")
        data = response.json()
        if data.get("success"):
            print(f"   ✅ Success!")
            print(f"   Image URL: {data.get('image_url')}")
            print(f"   Image Type: {data.get('image_type')}")

            # Try to access the image
            image_url = base_url + data.get('image_url')
            print(f"\n3. Testing image access...")
            print(f"   Accessing: {image_url}")
            img_response = requests.get(image_url)
            print(f"   Status: {img_response.status_code}")
            if img_response.status_code == 200:
                print(f"   ✅ Image accessible!")
                print(f"   Content-Type: {img_response.headers.get('Content-Type')}")
            else:
                print(f"   ❌ Image not accessible")
                print(f"   Error: {img_response.text[:200]}")
        else:
            print(f"   ❌ Failed: {data.get('error')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test TradeIQ image generation")
    parser.add_argument(
        '--http',
        action='store_true',
        help='Test via HTTP API (requires server running)'
    )
    parser.add_argument(
        '--dirs-only',
        action='store_true',
        help='Only test directory setup'
    )

    args = parser.parse_args()

    # Always test directories
    test_media_directories()

    if args.dirs_only:
        print("\n✅ Directory check complete!")
    elif args.http:
        test_http_api()
    else:
        test_image_generation()

    print("\n✅ All tests complete!")
    print("\nTo test via HTTP, run:")
    print("  python test_image_api.py --http")
    print("\nOr browse to: http://localhost:8000/media/charts/")
