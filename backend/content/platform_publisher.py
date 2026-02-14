# backend/content/platform_publisher.py - Multi-Platform Publishing Orchestrator
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("tradeiq.platform_publisher")


def publish_to_all_platforms(
    content: str,
    image_path: Optional[str] = None,
    image_url: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    post_type: str = "single"
) -> Dict[str, any]:
    """
    Publish content to multiple platforms in parallel.

    Args:
        content: Text content (or thread content for multi-post)
        image_path: Local file path to image (for Bluesky)
        image_url: URL to image (for reference)
        platforms: ["bluesky"] or None (defaults to all)
        post_type: "single" | "thread"

    Returns:
        {
            "success": True,
            "results": {
                "bluesky": {"uri": "...", "url": "..."}
            },
            "errors": []
        }
    """
    if platforms is None:
        platforms = ["bluesky"]

    results = {}
    errors = []

    logger.info(f"Publishing to platforms: {platforms}")
    logger.info(f"Content: {content[:100]}... (type: {post_type})")

    # Publish to Bluesky
    if "bluesky" in platforms:
        try:
            bluesky_result = _publish_to_bluesky(content, image_path, post_type)
            results["bluesky"] = bluesky_result

            if bluesky_result.get("success"):
                logger.info(f"Bluesky publish successful: {bluesky_result.get('url')}")
            else:
                error_msg = f"Bluesky: {bluesky_result.get('error', 'Unknown error')}"
                errors.append(error_msg)
                logger.error(error_msg)

        except Exception as e:
            error_msg = f"Bluesky: {str(e)}"
            logger.error(f"Bluesky publish failed: {e}", exc_info=True)
            errors.append(error_msg)
            results["bluesky"] = {"success": False, "error": str(e)}

    return {
        "success": len(errors) == 0,
        "results": results,
        "errors": errors,
        "platforms": platforms,
        "post_type": post_type
    }


def _publish_to_bluesky(
    content: str,
    image_path: Optional[str],
    post_type: str
) -> dict:
    """
    Publish to Bluesky via BlueskyPublisher.

    Args:
        content: Post text or thread content
        image_path: Optional image file path
        post_type: "single" | "thread"

    Returns:
        Publish result dict
    """
    from .bluesky import BlueskyPublisher

    try:
        publisher = BlueskyPublisher()

        if post_type == "thread":
            # Parse thread content
            if isinstance(content, str):
                # Split by separator
                if "\n\n---\n\n" in content:
                    posts = [p.strip() for p in content.split("\n\n---\n\n") if p.strip()]
                else:
                    posts = [content]
            elif isinstance(content, list):
                posts = content
            else:
                posts = [str(content)]

            # Publish thread (note: image only on first post for now)
            result = publisher.post_thread(posts)

            return {
                "success": True,
                "results": result,
                "url": result[0]["url"] if result else None
            }

        else:  # Single post
            if image_path:
                # Use post_with_image method
                result = publisher.post_with_image(
                    text=content,
                    image_path=image_path
                )
            else:
                # Regular text post
                result = publisher.post(content)

            return {
                "success": True,
                **result
            }

    except Exception as e:
        logger.error(f"Bluesky publishing error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def format_content_for_platform(content: str, platform: str) -> str:
    """
    Format content for specific platform requirements.

    Args:
        content: Original content text
        platform: "bluesky"

    Returns:
        Formatted content within platform limits
    """
    if platform == "bluesky":
        # Bluesky: 300 char limit
        if len(content) > 300:
            return content[:297] + "..."

    return content
