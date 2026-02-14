"""
Content Generation Tools using DeepSeek LLM
Upgraded with Few-Shot examples and Market Context RAG.
"""
from typing import Dict, Any, List, Optional
from agents.llm_client import get_llm_client
from agents.prompts import SYSTEM_PROMPT_CONTENT, MASTER_COMPLIANCE_RULES as COMPLIANCE_RULES
from .models import AIPersona, SocialPost
from .examples import get_examples
from .personas import CALM_ANALYST, DATA_NERD, TRADING_COACH, ALL_PERSONAS
from datetime import datetime


# ─── Persona config lookup ──────────────────────────────────────

_PERSONA_MAP = {
    "calm_analyst": CALM_ANALYST,
    "data_nerd": DATA_NERD,
    "trading_coach": TRADING_COACH,
}


def _resolve_persona(persona_id: str):
    """Resolve persona by name or UUID. Returns (config_dict, db_persona_or_None)."""
    # Try by name first (for multi-persona engine)
    config = _PERSONA_MAP.get(persona_id)
    if config:
        return config, None

    # Try by UUID (original behavior)
    try:
        persona = AIPersona.objects.get(id=persona_id)
        # Match to config by personality_type
        for cfg in ALL_PERSONAS:
            if cfg["personality_type"] == persona.personality_type:
                return cfg, persona
        # Fallback: build minimal config from DB persona
        return {
            "name": persona.name,
            "system_prompt": persona.system_prompt or SYSTEM_PROMPT_CONTENT,
            "tone": "professional",
            "voice_config": {
                "preferred_emojis": ["\U0001f4ca"],
                "hashtag_count": 2,
            },
        }, persona
    except (AIPersona.DoesNotExist, Exception):
        # Ultimate fallback: Calm Analyst
        return CALM_ANALYST, None


def generate_draft(
    persona_id: str,
    topic: str,
    platform: str = "bluesky",
    max_length: int = 300,
    market_context: Optional[Dict[str, Any]] = None,
    style: str = "insight",
) -> Dict[str, Any]:
    """
    Generate a social media post draft using DeepSeek.

    Upgraded with:
    1. Few-Shot examples from examples.py
    2. Market context RAG injection
    3. Style-specific generation strategy
    4. Anti-AI-pattern voice enforcement
    """
    config, db_persona = _resolve_persona(persona_id)
    persona_name = config["name"]
    emojis = config.get("voice_config", {}).get("preferred_emojis", ["\U0001f4ca"])
    hashtag_count = config.get("voice_config", {}).get("hashtag_count", 2)

    # Get few-shot examples
    persona_key = config.get("personality_type", persona_id)
    few_shot = get_examples(persona_key, style)

    # Build enhanced system prompt
    system_prompt = f"""{config.get('system_prompt', SYSTEM_PROMPT_CONTENT)}

## Your Voice Rules (STRICT)
- Tone: {config.get('tone', 'professional')}
- Emoji usage: ONLY use these: {', '.join(emojis)}
- Hashtags: exactly {hashtag_count} per post
- Max length: 300 characters (Bluesky)
- NEVER use corporate jargon or AI-obvious patterns
- NEVER start with "In today's" or "Let's dive into" or "Here's the thing"
- End with a genuine question or observation that invites reply
- Write like a real person who happens to be an expert, not a content bot

## Examples of your best posts:
{chr(10).join(f'- "{ex}"' for ex in few_shot[:3])}

## Platform: Bluesky
- Bluesky values authenticity, developer-friendly culture, and genuine discussion
- Avoid Twitter/X engagement-bait tactics ("THREAD", "RT if you agree")
- Use Bluesky's longer text capability for nuance
"""

    # Market context injection (RAG)
    context_block = ""
    if market_context:
        context_block = f"""
## Fresh Market Data (use this for specificity):
- Instrument: {market_context.get('instrument', 'N/A')}
- Current Price: {market_context.get('price', 'N/A')}
- Change: {market_context.get('change_pct', 'N/A')}%
- Key News: {market_context.get('news_summary', 'No recent news')}
- Sentiment: {market_context.get('sentiment', 'neutral')}
"""

    user_prompt = f"""{context_block}
Topic: {topic}
Style: {style}
{COMPLIANCE_RULES}

Generate ONE post. Raw text only, no quotes or prefix."""

    try:
        llm = get_llm_client()
        content = llm.simple_chat(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.7,
            max_tokens=150
        )

        content_text = content.strip().strip('"')
        if "\U0001f4ca Analysis by TradeIQ" not in content_text:
            content_text += "\n\n\U0001f4ca Analysis by TradeIQ | Not financial advice"

        if len(content_text) > max_length:
            content_text = content_text[:max_length - 3] + "..."

        return {
            "content": content_text,
            "persona_id": persona_id,
            "persona_name": persona_name,
            "platform": platform,
            "style": style,
            "length": len(content_text),
            "status": "draft",
        }
    except Exception as e:
        return {
            "error": str(e),
            "content": "",
            "status": "error",
        }


def generate_thread(
    persona_id: str,
    topic: str,
    num_posts: int = 3,
    platform: str = "bluesky",
    market_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a thread (multiple connected posts) using DeepSeek.
    Upgraded with few-shot examples.
    """
    num_posts = min(num_posts, 5)

    config, db_persona = _resolve_persona(persona_id)
    persona_name = config["name"]
    persona_key = config.get("personality_type", persona_id)
    few_shot = get_examples(persona_key, "thread_hook")

    system_prompt = f"""{config.get('system_prompt', SYSTEM_PROMPT_CONTENT)}

## Thread hook examples:
{chr(10).join(f'- "{ex}"' for ex in few_shot[:2])}
"""

    context_block = ""
    if market_context:
        context_block = f"""Market context:
- Instrument: {market_context.get('instrument', 'N/A')}
- Change: {market_context.get('change_pct', 'N/A')}%
"""

    prompt = f"""{context_block}Generate a {platform} thread about: {topic}

Persona: {persona_name}
Number of posts: {num_posts}

Requirements:
- Each post under 300 chars
- Posts should flow logically (1/{num_posts}, 2/{num_posts}, etc. format)
- {COMPLIANCE_RULES}
- Include data points
- Last post ends with: "\U0001f4ca Analysis by TradeIQ | Not financial advice"

Return JSON array with {num_posts} posts:
[
  {{"index": 1, "content": "..."}},
  {{"index": 2, "content": "..."}},
  ...
]"""

    try:
        llm = get_llm_client()
        response = llm.simple_chat(
            system_prompt=system_prompt,
            user_message=prompt,
            temperature=0.7,
            max_tokens=800,
        )

        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()

        import json
        posts = json.loads(response_text)

        if posts and isinstance(posts, list):
            last_post = posts[-1]
            if isinstance(last_post, dict) and "\U0001f4ca Analysis by TradeIQ" not in last_post.get("content", ""):
                last_post["content"] += "\n\n\U0001f4ca Analysis by TradeIQ | Not financial advice"

        return {
            "posts": posts,
            "persona_id": persona_id,
            "persona_name": persona_name,
            "platform": platform,
            "num_posts": len(posts) if isinstance(posts, list) else 0,
            "status": "draft",
        }
    except Exception as e:
        return {
            "error": str(e),
            "posts": [],
            "status": "error",
        }


def format_for_platform(content: str, platform: str) -> str:
    """Format content for specific platform requirements."""
    formatted = content.strip()

    if platform.lower() == "bluesky":
        if len(formatted) > 300:
            formatted = formatted[:297] + "..."
    elif platform.lower() == "twitter":
        if len(formatted) > 280:
            formatted = formatted[:277] + "..."

    return formatted
