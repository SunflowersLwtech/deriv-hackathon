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

    Decision flow:
      - If the post is about price movement AND we can fetch live chart
        data from Deriv/Finnhub → generate a matplotlib chart.
      - Otherwise → generate an AI image (Gemini) whose context matches
        the post content.

    Args:
        content_text: The social media post text
        analysis_report: Optional analysis report with market data
        persona_id: Persona ID for style preferences

    Returns:
        dict with image_url, image_path, image_alt_text, image_type, etc.
    """
    logger.info(f"Starting image generation for content: {content_text[:100]}...")

    try:
        # Step 1: Classify content (also checks data availability)
        classification = classify_content_for_image(content_text, analysis_report)
        image_type = classification["image_type"]

        logger.info(
            f"Classification: {image_type} "
            f"(confidence: {classification['confidence']:.2f}) "
            f"- {classification['reasoning']}"
        )

        # Step 2: Generate the appropriate image
        if image_type == "chart":
            chart_params = classification.get("chart_params", {})
            instrument = chart_params.get("instrument")

            # Fetch real-time price to use as current_price on the chart
            try:
                from market.tools import fetch_price_data
                live_data = fetch_price_data(instrument)
                if live_data and live_data.get("price"):
                    chart_params["current_price"] = live_data["price"]
                    logger.info(f"Live price for {instrument}: ${live_data['price']}")
            except Exception as e:
                logger.warning(f"Could not fetch live price for {instrument}: {e}")

            image_result = _generate_chart_image(classification, analysis_report)

            # If chart generation fails, fall back to AI image
            if not image_result.get("success"):
                logger.warning(
                    f"Chart generation failed for {instrument}, "
                    f"falling back to AI image: {image_result.get('error')}"
                )
                image_type = "ai_generated"
                image_result = _generate_ai_image(content_text, persona_id)
        else:
            # Not about price movement, or instrument not chartable → AI image
            image_result = _generate_ai_image(content_text, persona_id)

        # Step 3: Build response
        if image_result.get("success"):
            return {
                "image_url": image_result["image_url"],
                "image_path": image_result["image_path"],
                "image_alt_text": image_result["alt_text"],
                "image_type": image_type,
                "classification_reasoning": classification["reasoning"],
                "classification_confidence": classification["confidence"],
                "generated_at": datetime.now().isoformat(),
                "success": True
            }
        else:
            logger.error(f"Image generation failed: {image_result.get('error')}")
            return {
                "success": False,
                "error": image_result.get("error", "Unknown error"),
                "image_type": image_type,
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
