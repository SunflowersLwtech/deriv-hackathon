# backend/content/image_classifier.py - Content Classification for Image Type
import logging
import re
from typing import Any, Dict, Optional, Set
from agents.llm_client import get_llm_client

logger = logging.getLogger("tradeiq.image_classifier")

# Instruments we can actually fetch live data for (Deriv API + Finnhub)
CHARTABLE_INSTRUMENTS: Set[str] = {
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CHF",
    "GOLD", "XAU/USD", "SILVER",
    "BTC/USD", "ETH/USD",
    "Volatility 75", "Volatility 100", "Volatility 10",
}


def is_instrument_chartable(instrument: str) -> bool:
    """Check if we can fetch live chart data for this instrument."""
    if not instrument:
        return False
    normalized = instrument.upper().strip()
    for supported in CHARTABLE_INSTRUMENTS:
        if normalized == supported.upper():
            return True
    return False


def classify_content_for_image(
    content_text: str,
    analysis_report: Optional[dict] = None
) -> dict:
    """
    Classify if content needs a live chart vs an AI-generated image.

    Decision logic:
      1. Is this about price movement / charts?
      2. Can we actually fetch live data for the instrument?
      If BOTH yes -> "chart".  Otherwise -> "ai_generated".
    """
    try:
        quick_result = _quick_classify(content_text, analysis_report)
        if quick_result["confidence"] >= 0.9:
            result = quick_result
        else:
            result = _llm_classify(content_text, analysis_report)

        if result["image_type"] == "chart":
            chart_params = result.get("chart_params")
            instrument = chart_params.get("instrument") if chart_params else None

            if not instrument or not is_instrument_chartable(instrument):
                logger.info(
                    f"Content is about price movement but instrument "
                    f"'{instrument}' is not chartable. Falling back to AI image."
                )
                result["image_type"] = "ai_generated"
                result["reasoning"] = (
                    f"Price movement detected but no live data available for "
                    f"'{instrument or 'unknown'}'. Using AI image instead."
                )
                result["chart_params"] = None

        logger.info(
            f"Classification: {result['image_type']} "
            f"(confidence: {result['confidence']:.2f})"
        )
        return result

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return {
            "image_type": "ai_generated",
            "confidence": 0.5,
            "reasoning": f"Defaulted to AI image due to classification error: {str(e)}",
            "chart_params": None
        }


def _quick_classify(content_text: str, analysis_report: Optional[dict]) -> dict:
    """Fast rule-based classification using regex and keywords."""
    text_lower = content_text.lower()

    chart_patterns = [
        r'\b(btc|eth|eur|usd|gbp|gold|nasdaq|sp500)\b',
        r'\b\d+\.?\d*%',
        r'\$\d+[,\d]*\.?\d*[kmb]?',
        r'\b(dropped|fell|rose|gained|surged|crashed|rallied)\b',
        r'\b(support|resistance|breakout|breakdown)\b',
    ]

    ai_patterns = [
        r'\b(remember|tip|advice|lesson|learn|education)\b',
        r'\b(psychology|mindset|emotional|discipline|patience)\b',
        r'\b(risk management|strategy|planning)\b',
        r'\b(trading habit|trader|beginner)\b',
    ]

    chart_matches = sum(1 for pattern in chart_patterns if re.search(pattern, text_lower))
    ai_matches = sum(1 for pattern in ai_patterns if re.search(pattern, text_lower))

    if analysis_report and isinstance(analysis_report, dict):
        if analysis_report.get('instrument') and analysis_report.get('change_pct'):
            chart_matches += 2

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
        return {
            "image_type": "chart" if chart_matches > 0 else "ai_generated",
            "confidence": 0.5,
            "reasoning": "Ambiguous content, low confidence",
            "chart_params": _extract_chart_params(content_text, analysis_report) if chart_matches > 0 else None
        }


def _llm_classify(content_text: str, analysis_report: Optional[dict]) -> dict:
    """Use LLM to classify content for image type."""
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
            temperature=0.3,
            max_tokens=150
        )

        import json
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        if result.get("image_type") == "chart":
            result["chart_params"] = _extract_chart_params(content_text, analysis_report)
        else:
            result["chart_params"] = None

        return result

    except Exception as e:
        logger.error(f"LLM classification failed: {e}")
        return _quick_classify(content_text, analysis_report)


def _llm_extract_instrument(content_text: str) -> Optional[str]:
    """Use LLM to extract trading instrument from ambiguous content."""
    try:
        llm = get_llm_client()
        prompt = f"""Extract the trading instrument from this text. Return ONLY the symbol in format like:
- BTC/USD, ETH/USD (for crypto)
- EUR/USD, GBP/USD (for forex)
- GOLD, SILVER, OIL (for commodities)
- NASDAQ, S&P 500 (for indices)

If no specific instrument is mentioned, return "NONE".

Text: "{content_text}"

Instrument:"""

        response = llm.simple_chat(
            system_prompt="You are a financial instrument extractor. Be precise and concise.",
            user_message=prompt,
            temperature=0.1,
            max_tokens=20
        )

        instrument = response.strip().upper()
        if instrument and instrument != "NONE" and len(instrument) < 20:
            logger.info(f"LLM extracted instrument: {instrument}")
            return instrument

    except Exception as e:
        logger.warning(f"LLM instrument extraction failed: {e}")

    return None


def _extract_chart_params(content_text: str, analysis_report: Optional[dict]) -> Optional[Dict[str, Any]]:
    """Extract chart parameters from content and analysis report."""
    params: Dict[str, Any] = {}

    if analysis_report and isinstance(analysis_report, dict):
        params["instrument"] = analysis_report.get("instrument")
        params["current_price"] = analysis_report.get("current_price") or analysis_report.get("price")
        params["change_pct"] = analysis_report.get("change_pct") or analysis_report.get("change_percent")

        if all(params.values()):
            return params

    text_lower = content_text.lower()

    instruments = {
        'btc': 'BTC/USD', 'bitcoin': 'BTC/USD',
        'eth': 'ETH/USD', 'ethereum': 'ETH/USD',
        'sol': 'SOL/USD', 'solana': 'SOL/USD',
        'eur/usd': 'EUR/USD', 'eurusd': 'EUR/USD', 'eur': 'EUR/USD',
        'gbp/usd': 'GBP/USD', 'gbpusd': 'GBP/USD', 'gbp': 'GBP/USD',
        'usd/jpy': 'USD/JPY', 'usdjpy': 'USD/JPY',
        'aud/usd': 'AUD/USD', 'audusd': 'AUD/USD',
        'usd/chf': 'USD/CHF', 'usdchf': 'USD/CHF',
        'gold': 'GOLD', 'xau': 'GOLD', 'xau/usd': 'GOLD',
        'silver': 'SILVER', 'xag': 'SILVER',
        'nasdaq': 'NASDAQ', 'ndx': 'NASDAQ',
    }

    for key, value in instruments.items():
        if key in text_lower:
            params["instrument"] = value
            break

    if not params.get("instrument"):
        forex_match = re.search(r'\b([A-Z]{3})[/\s]([A-Z]{3})\b', content_text)
        if forex_match:
            params["instrument"] = f"{forex_match.group(1)}/{forex_match.group(2)}"

    if not params.get("instrument"):
        llm_instrument = _llm_extract_instrument(content_text)
        if llm_instrument:
            params["instrument"] = llm_instrument

    pct_match = re.search(r'([-+]?\d+\.?\d*)%', content_text)
    if pct_match:
        params["change_pct"] = float(pct_match.group(1))

    price_match = re.search(r'\$(\d+[,\d]*\.?\d*)([kmb]?)', content_text, re.IGNORECASE)
    if price_match:
        price_str = price_match.group(1).replace(',', '')
        multiplier_str = price_match.group(2).lower()
        price = float(price_str)
        if multiplier_str == 'k':
            price *= 1000
        elif multiplier_str == 'm':
            price *= 1_000_000
        elif multiplier_str == 'b':
            price *= 1_000_000_000
        params["current_price"] = price

    if params.get("instrument") and not params.get("current_price"):
        try:
            from market.tools import fetch_price_data
            price_data = fetch_price_data(params["instrument"])
            if price_data and price_data.get("price"):
                params["current_price"] = price_data["price"]
        except Exception as e:
            logger.warning(f"Failed to fetch real price: {e}")
            default_prices = {
                'BTC/USD': 95000, 'ETH/USD': 3500, 'EUR/USD': 1.0850,
                'GBP/USD': 1.2650, 'GOLD': 2400, 'NASDAQ': 18000,
            }
            params["current_price"] = default_prices.get(params["instrument"], 100)

    if params.get("instrument"):
        if params.get("change_pct") is None:
            params["change_pct"] = None
        if not params.get("current_price"):
            params["current_price"] = 100
        return params

    return None
