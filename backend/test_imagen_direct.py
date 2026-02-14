#!/usr/bin/env python
"""
Direct test of Imagen 4 API to diagnose issues.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradeiq.settings')
django.setup()

from django.conf import settings
from google import genai
from PIL import Image
import io

print("=" * 60)
print("Testing Imagen 4 API Directly")
print("=" * 60)

# Create client
client = genai.Client(api_key=settings.GOOGLE_GEMINI_API_KEY)

# Test prompts
test_prompt = """A professional financial trading visualization showing abstract market concepts.
Clean, minimalist design with navy blue and gold colors. Modern financial illustration style.
16:9 aspect ratio, suitable for social media."""

print(f"\nPrompt: {test_prompt}\n")

# Test different models
models_to_test = [
    'imagen-4.0-fast-generate-001',
    'imagen-4.0-generate-001',
    'gemini-2.0-flash-exp-image-generation',
]

for model_name in models_to_test:
    print(f"\n{'=' * 60}")
    print(f"Testing: {model_name}")
    print('=' * 60)

    try:
        if 'gemini' in model_name:
            # Use generate_content for Gemini models
            print("Method: generate_content")
            response = client.models.generate_content(
                model=model_name,
                contents=test_prompt,
                config={
                    'response_modalities': ['image'],
                }
            )

            print(f"Response type: {type(response)}")
            print(f"Has candidates: {hasattr(response, 'candidates')}")

            if hasattr(response, 'candidates'):
                print(f"Number of candidates: {len(response.candidates)}")
                for i, candidate in enumerate(response.candidates):
                    print(f"\nCandidate {i}:")
                    print(f"  Has content: {hasattr(candidate, 'content')}")
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        print(f"  Number of parts: {len(candidate.content.parts)}")
                        for j, part in enumerate(candidate.content.parts):
                            print(f"  Part {j}:")
                            print(f"    Has inline_data: {hasattr(part, 'inline_data')}")
                            if hasattr(part, 'inline_data'):
                                print(f"    Has data: {hasattr(part.inline_data, 'data')}")
                                if hasattr(part.inline_data, 'data'):
                                    data_len = len(part.inline_data.data) if part.inline_data.data else 0
                                    print(f"    Data length: {data_len} bytes")

                                    if data_len > 0:
                                        # Try to save image
                                        try:
                                            img = Image.open(io.BytesIO(part.inline_data.data))
                                            filename = f"test_{model_name.replace('/', '_')}.png"
                                            img.save(f"media/ai_images/{filename}")
                                            print(f"    SUCCESS! Saved to media/ai_images/{filename}")
                                            print(f"    Image size: {img.size}")
                                        except Exception as save_error:
                                            print(f"    ERROR saving image: {save_error}")

        else:
            # Use generate_images for Imagen models
            print("Method: generate_images")
            response = client.models.generate_images(
                model=model_name,
                prompt=test_prompt,
                config={
                    'number_of_images': 1,
                    'aspect_ratio': '16:9',
                }
            )

            print(f"Response type: {type(response)}")
            print(f"Has generated_images: {hasattr(response, 'generated_images')}")

            if hasattr(response, 'generated_images'):
                print(f"Number of images: {len(response.generated_images)}")
                for i, img_data in enumerate(response.generated_images):
                    print(f"\nImage {i}:")
                    print(f"  Type: {type(img_data)}")
                    print(f"  Has image attr: {hasattr(img_data, 'image')}")

                    if hasattr(img_data, 'image'):
                        print(f"  Has image_bytes: {hasattr(img_data.image, 'image_bytes')}")
                        if hasattr(img_data.image, 'image_bytes') and img_data.image.image_bytes:
                            img_bytes = img_data.image.image_bytes
                            print(f"  Image bytes length: {len(img_bytes)}")

                            # Try to save image
                            try:
                                img = Image.open(io.BytesIO(img_bytes))
                                filename = f"test_{model_name.replace('/', '_')}.png"
                                img.save(f"media/ai_images/{filename}")
                                print(f"  SUCCESS! Saved to media/ai_images/{filename}")
                                print(f"  Image size: {img.size}")
                            except Exception as save_error:
                                print(f"  ERROR saving image: {save_error}")

        print(f"\nFull response object attributes:")
        print(f"  {[attr for attr in dir(response) if not attr.startswith('_')][:10]}")

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)[:300]}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

print("\n" + "=" * 60)
print("Testing Complete")
print("=" * 60)
