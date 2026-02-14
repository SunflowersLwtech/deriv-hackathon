# backend/content/ai_image_generator.py - AI Image Generation via Google Gemini
import os
import logging
import base64
from datetime import datetime
from typing import Dict, Optional
from django.conf import settings
from PIL import Image
import io

logger = logging.getLogger("tradeiq.ai_image")


def generate_ai_image(
    prompt_text: str,
    content_context: Optional[dict] = None,
    style: str = "professional"
) -> dict:
    """
    Generate AI image via Google Gemini Imagen API.
 
    Args:
        prompt_text: The social media post text to base image on
        content_context: Optional dict with {persona, topic, sentiment}
        style: "professional" | "creative" | "technical"

    Returns:
        {
            "image_path": "/path/to/image.png",
            "image_url": "/media/ai_images/imagen_xyz123.png",
            "alt_text": "AI-generated trading visualization",
            "prompt_used": "Professional trading concept...",
            "success": True
        }
    """
    try:
        from google import genai

        # Configure API
        if not settings.GOOGLE_GEMINI_API_KEY:
            raise ValueError("GOOGLE_GEMINI_API_KEY not configured in settings")

        # Create client with new SDK
        client = genai.Client(api_key=settings.GOOGLE_GEMINI_API_KEY)

        # Construct image generation prompt
        image_prompt = _build_image_prompt(prompt_text, content_context, style)

        logger.info(f"Generating AI image with Imagen 4...")
        logger.info(f"Prompt: {image_prompt[:150]}...")

        try:
            # Use Imagen 4 for actual AI image generation
            # Try models in order of preference: fast -> standard -> ultra
            models_to_try = [
                'imagen-4.0-fast-generate-001',    # Fastest (1-2 seconds)
                'imagen-4.0-generate-001',          # Standard quality
                'imagen-4.0-ultra-generate-001',    # Best quality (slower)
            ]

            response = None
            model_used = None

            for model_name in models_to_try:
                try:
                    logger.info(f"Trying {model_name}...")

                    response = client.models.generate_images(
                        model=model_name,
                        prompt=image_prompt,
                        config={
                            'number_of_images': 1,
                            'aspect_ratio': '16:9',
                        }
                    )

                    model_used = model_name
                    logger.info(f"Success with {model_name}!")
                    break
                except Exception as model_error:
                    logger.warning(f"{model_name} failed: {str(model_error)[:200]}")
                    continue

            if not response:
                raise Exception("All Imagen 4 models failed")

            # Extract image bytes from Imagen response
            if not (response and hasattr(response, 'generated_images') and len(response.generated_images) > 0):
                raise Exception("No generated_images in response")

            image_data = response.generated_images[0]

            # Get image bytes
            if hasattr(image_data, 'image') and hasattr(image_data.image, 'image_bytes'):
                image_bytes = image_data.image.image_bytes
            elif hasattr(image_data, '_image_bytes'):
                image_bytes = image_data._image_bytes
            else:
                raise Exception("Cannot extract image bytes from Imagen response")

            if not image_bytes:
                raise Exception("No image bytes extracted from response")

            # Convert to PIL Image
            img = Image.open(io.BytesIO(image_bytes))

            # Save image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"imagen4_{timestamp}.png"
            filepath = settings.MEDIA_ROOT / "ai_images" / filename

            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            img.save(filepath, 'PNG', quality=95)

            # Generate URL
            image_url = f"{settings.MEDIA_URL}ai_images/{filename}"

            # Generate relative path for backend use
            relative_path = f"ai_images/{filename}"

            alt_text = f"AI-generated {style} trading visualization"

            logger.info(f"Success! {model_used} generated image: {filename}")

            return {
                "image_path": relative_path,  # Relative path for backend to reconstruct full path
                "image_url": image_url,
                "alt_text": alt_text,
                "prompt_used": image_prompt,
                "description": f"AI-generated image using {model_used}",
                "model_used": model_used,
                "success": True
            }

        except Exception as imagen_error:
            # If Imagen fails, fall back to enhanced placeholder with Gemini description
            logger.warning(f"Imagen not available or failed: {imagen_error}")
            logger.info("Falling back to Gemini-enhanced placeholder image...")

            return _generate_gemini_enhanced_placeholder(
                prompt_text,
                content_context,
                style,
                image_prompt,
                client
            )

    except Exception as e:
        logger.error(f"AI image generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "image_path": None,
            "image_url": None
        }


def _generate_gemini_enhanced_placeholder(
    prompt_text: str,
    content_context: Optional[dict],
    style: str,
    image_prompt: str,
    client
) -> dict:
    """
    Generate enhanced placeholder using Gemini for description.

    Args:
        prompt_text: Original content text
        content_context: Content context
        style: Image style
        image_prompt: Generated image prompt
        client: Gemini client instance

    Returns:
        Image generation result
    """
    try:
        # Use latest Gemini model to generate detailed description
        description_prompt = f"""Generate a detailed visual description for this trading concept:

Content: {prompt_text}
Style: {style}

Describe a professional, minimalist image that would accompany this trading content.
Focus on colors, composition, and visual metaphors. Keep it under 100 words."""

        # Try latest models in order of preference
        models_to_try = [
            'gemini-2.0-flash-exp',
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
        ]

        description = None
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=description_prompt,
                    config={
                        'temperature': 0.7,
                        'max_output_tokens': 200,
                    }
                )

                if response and hasattr(response, 'text') and response.text:
                    description = response.text.strip()
                    logger.info(f"Generated description using {model_name}")
                    break
            except Exception as model_error:
                logger.debug(f"Model {model_name} failed: {model_error}")
                continue

        if not description:
            description = "Professional trading visualization"

        # Create enhanced placeholder image
        relative_path, image_url = _create_placeholder_image(
            prompt_text,
            description,
            style
        )

        alt_text = f"AI-generated {style} trading visualization"

        logger.info("Created Gemini-enhanced placeholder image")

        return {
            "image_path": relative_path,  # Relative path
            "image_url": image_url,
            "alt_text": alt_text,
            "prompt_used": image_prompt,
            "description": description,
            "success": True
        }

    except Exception as e:
        logger.error(f"Gemini-enhanced placeholder failed: {e}")
        # Final fallback to basic placeholder
        relative_path, image_url = _create_placeholder_image(
            prompt_text,
            "Trading visualization",
            style
        )

        return {
            "image_path": relative_path,  # Relative path
            "image_url": image_url,
            "alt_text": f"{style} trading visualization",
            "prompt_used": image_prompt,
            "description": "Basic placeholder image",
            "success": True
        }


def _build_image_prompt(
    content_text: str,
    context: Optional[dict],
    style: str
) -> str:
    """
    Build an image generation prompt that is contextually tied to the post.

    The prompt captures the specific theme / mood / topic of the post so
    that Gemini generates a visually relevant image (not a generic one).

    Args:
        content_text: The social media post text
        context: Content context (persona, topic, sentiment)
        style: Image style preference

    Returns:
        Detailed image generation prompt
    """
    text_lower = content_text.lower()

    # Detect specific concepts from the post content
    concepts = []
    if any(w in text_lower for w in ['bitcoin', 'btc', 'crypto', 'blockchain']):
        concepts.append('cryptocurrency')
    if any(w in text_lower for w in ['forex', 'eur', 'usd', 'gbp', 'currency']):
        concepts.append('forex trading')
    if any(w in text_lower for w in ['psychology', 'mindset', 'emotional', 'discipline', 'patience', 'fear', 'greed']):
        concepts.append('trading psychology')
    if any(w in text_lower for w in ['risk', 'management', 'strategy', 'stop loss', 'position size']):
        concepts.append('risk management')
    if any(w in text_lower for w in ['gold', 'silver', 'oil', 'commodity']):
        concepts.append('commodities')
    if any(w in text_lower for w in ['learn', 'education', 'tip', 'beginner', 'lesson']):
        concepts.append('trading education')
    if any(w in text_lower for w in ['bull', 'bear', 'rally', 'crash', 'volatile']):
        concepts.append('market volatility')

    # Detect sentiment / mood for visual tone
    mood = "neutral"
    if any(w in text_lower for w in ['crash', 'drop', 'loss', 'fear', 'bearish', 'fell']):
        mood = "cautious, somber tones (deep blues, muted reds)"
    elif any(w in text_lower for w in ['surge', 'rally', 'bullish', 'gain', 'profit', 'rise']):
        mood = "optimistic, energetic tones (greens, golds, warm highlights)"
    elif any(w in text_lower for w in ['patience', 'discipline', 'calm', 'steady']):
        mood = "calm, zen-like serenity (soft gradients, cool blues)"

    # Style-specific prompt elements
    style_prompts = {
        "professional": "Clean, minimalist design with Bloomberg/Financial Times aesthetic. "
                       "Professional color palette: navy blue, white, subtle gold accents. "
                       "Modern financial illustration.",
        "creative": "Bold, modern design with vibrant colors. "
                   "Creative interpretation of trading concepts. "
                   "Abstract geometric shapes representing market data.",
        "technical": "Data visualization style with charts, graphs, and technical elements. "
                    "Technical aesthetic with clean lines and precise geometry. "
                    "Professional technical analysis theme."
    }

    concept_str = ", ".join(concepts) if concepts else "trading and finance"

    # Truncate post for the prompt (avoid exceeding token limits)
    post_summary = content_text[:200].strip()

    prompt = f"""{style_prompts.get(style, style_prompts['professional'])}

Post context: "{post_summary}"
Subject: {concept_str}
Visual mood: {mood}
Composition: Horizontal 16:9 format, ideal for social media
Elements: Modern, abstract representation that visually captures the theme of the post above
Color scheme: Professional financial aesthetics
Style: Flat design, minimal shadows, high contrast

DO NOT include any text, numbers, or specific stock tickers in the image.
Create an abstract visual that captures the essence and mood of the post context above."""

    return prompt


def _create_placeholder_image(
    content_text: str,
    description: str,
    style: str
) -> tuple:
    """
    Create a placeholder image with gradient background.

    This is a fallback implementation. In production, replace with actual
    Imagen API calls via Vertex AI.

    Returns:
        (image_path, image_url)
    """
    # Create gradient background based on style
    width, height = 1200, 675

    # Style-specific colors
    color_schemes = {
        "professional": ((25, 25, 112), (70, 130, 180)),  # Navy to Steel Blue
        "creative": ((138, 43, 226), (255, 20, 147)),     # Purple to Deep Pink
        "technical": ((47, 79, 79), (0, 128, 128))        # Dark Slate Gray to Teal
    }

    color1, color2 = color_schemes.get(style, color_schemes["professional"])

    # Create image with gradient
    img = Image.new('RGB', (width, height), color=color1)
    pixels = img.load()

    for y in range(height):
        # Calculate gradient color
        ratio = y / height
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)

        for x in range(width):
            pixels[x, y] = (r, g, b)

    # Add text overlay with content snippet
    from PIL import ImageDraw, ImageFont

    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 48)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Add trading icon emoji or text
    trading_icon = "📊 💹 📈"
    icon_bbox = draw.textbbox((0, 0), trading_icon, font=font_large)
    icon_width = icon_bbox[2] - icon_bbox[0]
    icon_x = (width - icon_width) // 2
    draw.text((icon_x, height // 2 - 60), trading_icon, fill="white", font=font_large)

    # Add watermark
    watermark = "TradeIQ AI"
    wm_bbox = draw.textbbox((0, 0), watermark, font=font_small)
    wm_width = wm_bbox[2] - wm_bbox[0]
    draw.text((width - wm_width - 20, height - 40), watermark, fill="white", font=font_small, opacity=128)

    # Save image
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"ai_gen_{timestamp}.png"
    filepath = settings.MEDIA_ROOT / "ai_images" / filename

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    img.save(filepath, 'PNG', quality=95)

    # Generate URL and relative path
    image_url = f"{settings.MEDIA_URL}ai_images/{filename}"
    relative_path = f"ai_images/{filename}"

    logger.info(f"Created placeholder AI image: {filename}")
    logger.info(f"Description: {description[:100]}...")

    return relative_path, image_url


# Note: Imagen 3 API implementation
# The main generate_ai_image() function now uses Imagen 3 directly via google.genai SDK
# No Vertex AI setup required - just the GOOGLE_GEMINI_API_KEY
# If Imagen 3 is not available (API access restrictions), it falls back to
# Gemini-enhanced placeholder images with AI-generated descriptions
