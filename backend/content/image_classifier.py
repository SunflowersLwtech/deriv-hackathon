# backend/content/image_classifier.py - Content Classification for Image Type
import logging
import re
from typing import Dict, Optional
from agents.llm_client import get_llm_client

logger = logging.getLogger("tradeiq.image_classifier")


def classify_content_for_image(
    content_text: str,
    analysis_report: Optional[dict] = None
) -> dict:
    """
    Classify if content needs chart vs AI-generated image.

    Uses LLM to intelligently determine the best visual accompaniment
    based on content type.

    Args:
        content_text: The social media post text
        analysis_report: Optional analysis report with market data

    Returns:
        {
            "image_type": "chart" | "ai_generated",
            "confidence": 0.95,
            "reasoning": "Content mentions specific price movement",
            "chart_params": {
                "instrument": "BTC/USD",
                "current_price": 95000,
                "change_pct": -5.2,
                "highlight_event": "5% drop"
            } | None
        }
    """
    try:
        # Quick rule-based classification first (fast path)
        quick_result = _quick_classify(content_text, analysis_report)
        if quick_result["confidence"] >= 0.9:
            logger.info(f"Quick classification: {quick_result['image_type']} (confidence: {quick_result['confidence']})")
            return quick_result

        # Use LLM for ambiguous cases
        llm_result = _llm_classify(content_text, analysis_report)
        logger.info(f"LLM classification: {llm_result['image_type']} (confidence: {llm_result['confidence']})")
        return llm_result

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        # Default to AI-generated image on error
        return {
            "image_type": "ai_generated",
            "confidence": 0.5,
            "reasoning": f"Defaulted to AI image due to classification error: {str(e)}",
            "chart_params": None
        }


def _quick_classify(content_text: str, analysis_report: Optional[dict]) -> dict:
    """
    Fast rule-based classification using regex and keywords.

    Returns classification with confidence score.
    """
    text_lower = content_text.lower()

    # Chart indicators (high confidence patterns)
    chart_patterns = [
        r'\b(btc|eth|eur|usd|gbp|gold|nasdaq|sp500)\b',  # Instrument mentions
        r'\b\d+\.?\d*%',  # Percentage changes
        r'\$\d+[,\d]*\.?\d*[kmb]?',  # Price levels
        r'\b(dropped|fell|rose|gained|surged|crashed|rallied)\b',  # Movement verbs
        r'\b(support|resistance|breakout|breakdown)\b',  # Technical terms
    ]

    # AI image indicators (education, psychology, general concepts)
    ai_patterns = [
        r'\b(remember|tip|advice|lesson|learn|education)\b',
        r'\b(psychology|mindset|emotional|discipline|patience)\b',
        r'\b(risk management|strategy|planning)\b',
        r'\b(trading habit|trader|beginner)\b',
    ]

    chart_matches = sum(1 for pattern in chart_patterns if re.search(pattern, text_lower))
    ai_matches = sum(1 for pattern in ai_patterns if re.search(pattern, text_lower))

    # If analysis_report has specific market data, it's likely chart-worthy
    if analysis_report and isinstance(analysis_report, dict):
        if analysis_report.get('instrument') and analysis_report.get('change_pct'):
            chart_matches += 2

    # Determine classification
    if chart_matches >= 2 and chart_matches > ai_matches:
        return {
            "image_type": "chart",
            "confidence": min(0.9, 0.7 + (chart_matches * 0.1)),
            "reasoning": f"Found {chart_matches} chart indicators (price/instrument mentions)",
            "chart_params": _extract_chart_params(content_text, analysis_report)
        }
    elif ai_matches >= 2 and ai_matches > chart_matches:
        return {
            "image_type": "ai_generated",
            "confidence": min(0.9, 0.7 + (ai_matches * 0.1)),
            "reasoning": f"Found {ai_matches} educational/psychological indicators",
            "chart_params": None
        }
    else:
        # Ambiguous - return low confidence to trigger LLM classification
        return {
            "image_type": "chart" if chart_matches > 0 else "ai_generated",
            "confidence": 0.5,
            "reasoning": "Ambiguous content, low confidence",
            "chart_params": _extract_chart_params(content_text, analysis_report) if chart_matches > 0 else None
        }


def _llm_classify(content_text: str, analysis_report: Optional[dict]) -> dict:
    """
    Use LLM to classify content for image type.

    More accurate but slower than rule-based classification.
    """
    system_prompt = """You are classifying trading content to determine the best visual accompaniment.

CHART indicators:
- Specific instruments mentioned (BTC, EUR/USD, GOLD, etc.)
- Price levels or percentage changes
- Market movements (crash, surge, drop, rally, breakout)
- Technical analysis terms (support, resistance, RSI, volume)

AI IMAGE indicators:
- Trading psychology or mindset topics
- Educational content or tips
- General risk management principles
- Trader habits or discipline
- Emotional trading discussions

Respond with JSON:
{
    "image_type": "chart" or "ai_generated",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}"""

    analysis_context = ""
    if analysis_report and isinstance(analysis_report, dict):
        analysis_context = f"\n\nAnalysis Report:\n{str(analysis_report)}"

    user_prompt = f"""Classify this trading content:

"{content_text}"{analysis_context}

Return JSON only."""

    try:
        llm = get_llm_client()
        response = llm.simple_chat(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.3,  # Low temperature for consistent classification
            max_tokens=150
        )

        # Parse JSON response
        import json
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        # Add chart params if chart type
        if result.get("image_type") == "chart":
            result["chart_params"] = _extract_chart_params(content_text, analysis_report)
        else:
            result["chart_params"] = None

        return result

    except Exception as e:
        logger.error(f"LLM classification failed: {e}")
        # Fallback to quick classification
        return _quick_classify(content_text, analysis_report)


def _extract_chart_params(content_text: str, analysis_report: Optional[dict]) -> Optional[dict]:
    """
    Extract chart parameters from content and analysis report.

    Returns dict with instrument, price, change_pct, etc.
    """
    params = {}

    # Try to extract from analysis_report first (most reliable)
    if analysis_report and isinstance(analysis_report, dict):
        params["instrument"] = analysis_report.get("instrument")
        params["current_price"] = analysis_report.get("current_price") or analysis_report.get("price")
        params["change_pct"] = analysis_report.get("change_pct") or analysis_report.get("change_percent")

        if all(params.values()):
            return params

    # Try to extract from content text
    text_lower = content_text.lower()

    # Extract instrument
    instruments = {
        'btc': 'BTC/USD',
        'bitcoin': 'BTC/USD',
        'eth': 'ETH/USD',
        'ethereum': 'ETH/USD',
        'eur': 'EUR/USD',
        'gold': 'GOLD',
        'nasdaq': 'NASDAQ',
        'sp500': 'S&P 500'
    }

    for key, value in instruments.items():
        if key in text_lower:
            params["instrument"] = value
            break

    # Extract percentage change
    pct_match = re.search(r'([-+]?\d+\.?\d*)%', content_text)
    if pct_match:
        params["change_pct"] = float(pct_match.group(1))

    # Extract price
    price_match = re.search(r'\$(\d+[,\d]*\.?\d*)[kmb]?', content_text, re.IGNORECASE)
    if price_match:
        price_str = price_match.group(1).replace(',', '')
        params["current_price"] = float(price_str)

    # Only return params if we have minimum required data
    if params.get("instrument") and params.get("change_pct") is not None:
        # Use default price if not found
        if not params.get("current_price"):
            default_prices = {
                'BTC/USD': 95000,
                'ETH/USD': 3500,
                'EUR/USD': 1.0850,
                'GOLD': 2400
            }
            params["current_price"] = default_prices.get(params["instrument"], 100)

        return params

    return None
