# backend/content/image_orchestrator.py - Image Generation Orchestrator
import logging
from datetime import datetime
from typing import Dict, Optional
from .image_classifier import classify_content_for_image
from .chart_generator import generate_market_chart
from .ai_image_generator import generate_ai_image

logger = logging.getLogger("tradeiq.image_orchestrator")


def generate_image_for_content(
    content_text: str,
    analysis_report: Optional[dict] = None,
    persona_id: str = "calm_analyst"
) -> dict:
    """
    Main orchestrator: classify content → generate appropriate image.

    This is the primary entry point for image generation. It:
    1. Classifies the content to determine image type
    2. Generates either a chart or AI image based on classification
    3. Returns comprehensive image metadata

    Args:
        content_text: The social media post text
        analysis_report: Optional analysis report with market data
        persona_id: Persona ID for style preferences

    Returns:
        {
            "image_url": "http://localhost:8000/media/charts/BTC_20260214.png",
            "image_path": "/full/path/to/image.png",
            "image_alt_text": "BTC/USD chart showing 5% decline",
            "image_type": "chart" | "ai_generated",
            "classification_reasoning": "Content mentions specific price movement",
            "classification_confidence": 0.95,
            "generated_at": "2026-02-14T10:30:00Z",
            "success": True
        }
    """
    logger.info(f"Starting image generation for content: {content_text[:100]}...")

    try:
        # Step 1: Classify content to determine image type
        classification = classify_content_for_image(content_text, analysis_report)

        logger.info(
            f"Classification: {classification['image_type']} "
            f"(confidence: {classification['confidence']:.2f})"
        )

        # Step 2: Generate appropriate image based on classification
        if classification["image_type"] == "chart":
            image_result = _generate_chart_image(classification, analysis_report)
        else:
            image_result = _generate_ai_image(content_text, persona_id)

        # Step 3: Combine results
        if image_result.get("success"):
            return {
                "image_url": image_result["image_url"],
                "image_path": image_result["image_path"],
                "image_alt_text": image_result["alt_text"],
                "image_type": classification["image_type"],
                "classification_reasoning": classification["reasoning"],
                "classification_confidence": classification["confidence"],
                "generated_at": datetime.now().isoformat(),
                "success": True
            }
        else:
            # Image generation failed
            logger.error(f"Image generation failed: {image_result.get('error')}")
            return {
                "success": False,
                "error": image_result.get("error", "Unknown error"),
                "image_type": classification["image_type"],
                "classification_reasoning": classification["reasoning"]
            }

    except Exception as e:
        logger.error(f"Image orchestration failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "image_url": None,
            "image_path": None
        }


def _generate_chart_image(classification: dict, analysis_report: Optional[dict]) -> dict:
    """
    Generate market chart image using chart_generator.

    Args:
        classification: Classification result with chart_params
        analysis_report: Optional analysis report

    Returns:
        Chart generation result
    """
    chart_params = classification.get("chart_params", {})

    if not chart_params:
        logger.warning("Chart selected but no chart parameters available")
        # Try to extract from analysis_report
        if analysis_report:
            chart_params = {
                "instrument": analysis_report.get("instrument", "UNKNOWN"),
                "current_price": analysis_report.get("current_price") or analysis_report.get("price", 100),
                "change_pct": analysis_report.get("change_pct") or analysis_report.get("change_percent", 0)
            }

    # Ensure required parameters
    if not chart_params.get("instrument"):
        logger.error("Cannot generate chart without instrument")
        return {
            "success": False,
            "error": "Missing required chart parameter: instrument"
        }

    # Set defaults for missing parameters
    if not chart_params.get("current_price"):
        chart_params["current_price"] = 100
    if chart_params.get("change_pct") is None:
        chart_params["change_pct"] = 0

    logger.info(f"Generating chart for {chart_params['instrument']}")

    try:
        result = generate_market_chart(
            instrument=chart_params["instrument"],
            current_price=chart_params["current_price"],
            change_pct=chart_params["change_pct"],
            time_range=chart_params.get("time_range", "24h"),
            annotations=chart_params.get("annotations"),
            analysis_report=analysis_report
        )

        return result

    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        return {
            "success": False,
            "error": f"Chart generation failed: {str(e)}"
        }


def _generate_ai_image(content_text: str, persona_id: str) -> dict:
    """
    Generate AI image using ai_image_generator.

    Args:
        content_text: Post content
        persona_id: Persona for style

    Returns:
        AI image generation result
    """
    # Map persona to style
    persona_styles = {
        "calm_analyst": "professional",
        "data_nerd": "technical",
        "trading_coach": "creative"
    }

    style = persona_styles.get(persona_id, "professional")

    logger.info(f"Generating AI image with style: {style}")

    try:
        result = generate_ai_image(
            prompt_text=content_text,
            content_context={"persona": persona_id},
            style=style
        )

        return result

    except Exception as e:
        logger.error(f"AI image generation failed: {e}")
        return {
            "success": False,
            "error": f"AI image generation failed: {str(e)}"
        }


def batch_generate_images(
    content_items: list,
    analysis_reports: Optional[list] = None
) -> list:
    """
    Generate images for multiple content items in batch.

    Useful for pre-generating images for scheduled posts.

    Args:
        content_items: List of content text strings
        analysis_reports: Optional list of analysis reports (same length as content_items)

    Returns:
        List of image generation results
    """
    results = []

    for i, content in enumerate(content_items):
        report = None
        if analysis_reports and i < len(analysis_reports):
            report = analysis_reports[i]

        result = generate_image_for_content(content, report)
        results.append(result)

        logger.info(f"Batch: Generated image {i+1}/{len(content_items)}")

    return results
