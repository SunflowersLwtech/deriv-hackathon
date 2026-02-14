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
    Main orchestrator: classify content -> generate appropriate image.

    If the post is about price movement AND we can fetch live chart data
    -> generate a matplotlib chart.
    Otherwise -> generate an AI image (Gemini) whose context matches the post.
    """
    logger.info(f"Starting image generation for content: {content_text[:100]}...")

    try:
        classification = classify_content_for_image(content_text, analysis_report)
        image_type = classification["image_type"]

        logger.info(
            f"Classification: {image_type} "
            f"(confidence: {classification['confidence']:.2f}) "
            f"- {classification['reasoning']}"
        )

        if image_type == "chart":
            chart_params = classification.get("chart_params", {})
            instrument = chart_params.get("instrument")

            try:
                from market.tools import fetch_price_data
                live_data = fetch_price_data(instrument)
                if live_data and live_data.get("price"):
                    chart_params["current_price"] = live_data["price"]
                    logger.info(f"Live price for {instrument}: ${live_data['price']}")
            except Exception as e:
                logger.warning(f"Could not fetch live price for {instrument}: {e}")

            image_result = _generate_chart_image(classification, analysis_report)

            if not image_result.get("success"):
                logger.warning(
                    f"Chart generation failed for {instrument}, "
                    f"falling back to AI image: {image_result.get('error')}"
                )
                image_type = "ai_generated"
                image_result = _generate_ai_image(content_text, persona_id)
        else:
            image_result = _generate_ai_image(content_text, persona_id)

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
    """Generate market chart image using chart_generator."""
    chart_params = classification.get("chart_params", {})

    if not chart_params:
        if analysis_report:
            chart_params = {
                "instrument": analysis_report.get("instrument", "UNKNOWN"),
                "current_price": analysis_report.get("current_price") or analysis_report.get("price", 100),
                "change_pct": analysis_report.get("change_pct") or analysis_report.get("change_percent", 0)
            }

    if not chart_params.get("instrument"):
        return {"success": False, "error": "Missing required chart parameter: instrument"}

    if not chart_params.get("current_price"):
        chart_params["current_price"] = 100
    if chart_params.get("change_pct") is None:
        chart_params["change_pct"] = 0

    logger.info(f"Generating chart for {chart_params['instrument']}")

    try:
        return generate_market_chart(
            instrument=chart_params["instrument"],
            current_price=chart_params["current_price"],
            change_pct=chart_params["change_pct"],
            time_range=chart_params.get("time_range", "24h"),
            annotations=chart_params.get("annotations"),
            analysis_report=analysis_report
        )
    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        return {"success": False, "error": f"Chart generation failed: {str(e)}"}


def _generate_ai_image(content_text: str, persona_id: str) -> dict:
    """Generate AI image using ai_image_generator."""
    persona_styles = {
        "calm_analyst": "professional",
        "data_nerd": "technical",
        "trading_coach": "creative"
    }

    style = persona_styles.get(persona_id, "professional")
    logger.info(f"Generating AI image with style: {style}")

    try:
        return generate_ai_image(
            prompt_text=content_text,
            content_context={"persona": persona_id},
            style=style
        )
    except Exception as e:
        logger.error(f"AI image generation failed: {e}")
        return {"success": False, "error": f"AI image generation failed: {str(e)}"}
