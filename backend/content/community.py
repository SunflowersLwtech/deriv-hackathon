"""
Bluesky Community Interaction Engine

Bluesky differs from X/LinkedIn:
1. Transparent algorithms — Custom Feeds are user-controlled
2. Decentralized — content discovery depends on community reposts
3. Anti engagement-bait — community culture rejects traditional social tricks
4. Developer-friendly — AT Protocol Labeler mechanism

Strategy:
- Build influence through meaningful replies, not broadcasting
- Track trading/finance topic trends
- Provide professional, selfless analysis under relevant posts
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger("tradeiq.community")


def discover_trending_topics(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Discover trending trading/finance topics on Bluesky.

    Method:
    1. Search posts via search_posts() for relevant keywords
    2. Sort by engagement
    3. Extract topic keywords
    """
    from content.bluesky import BlueskyPublisher

    publisher = BlueskyPublisher()
    topics = []

    search_terms = [
        "forex trading", "crypto market", "BTC price",
        "trading psychology", "market analysis", "EUR USD",
    ]

    for term in search_terms:
        try:
            results = publisher.search_posts(term, limit=5)
            if results:
                for post in results:
                    topics.append({
                        "term": term,
                        "text": (post.get("text") or "")[:200],
                        "author": post.get("author", ""),
                        "likes": post.get("like_count", 0),
                        "replies": post.get("reply_count", 0),
                        "uri": post.get("uri", ""),
                    })
        except Exception as exc:
            logger.warning("Search failed for '%s': %s", term, exc)

    topics.sort(key=lambda t: t.get("likes", 0) + t.get("replies", 0), reverse=True)
    return topics[:limit]


def generate_reply_draft(
    original_post: Dict[str, Any],
    persona_name: str = "calm_analyst",
) -> Dict[str, Any]:
    """
    Generate a valuable reply draft for someone else's post.

    Strategy:
    - Provide data or analysis that supplements the original
    - Not just "agree" or "great post"
    - Demonstrate expertise, build trust
    - Maintain persona voice consistency
    """
    from agents.llm_client import get_llm_client
    from content.examples import get_examples

    persona_examples = get_examples(persona_name, "insight")

    system_prompt = f"""You are generating a reply to someone's trading-related post on Bluesky.

Rules:
- Add VALUE: data, analysis, a different perspective, or a follow-up question
- Do NOT just agree or compliment ("Great post!", "So true!")
- Keep it under 200 characters
- Be genuine, not promotional
- Never mention TradeIQ or any brand
- Match this voice style: {persona_examples[0] if persona_examples else 'professional, data-driven'}
"""

    user_prompt = f"""Original post: "{original_post.get('text', '')}"
Author: @{original_post.get('author', '')}

Generate a valuable reply that adds to the conversation."""

    try:
        llm = get_llm_client()
        reply = llm.simple_chat(system_prompt, user_prompt, max_tokens=100)
        return {
            "reply_text": reply.strip().strip('"'),
            "original_uri": original_post.get("uri", ""),
            "persona": persona_name,
            "status": "draft",
        }
    except Exception as exc:
        return {"error": str(exc)}


def generate_trend_content(
    trending_topics: List[Dict[str, Any]],
    persona_name: str = "calm_analyst",
) -> Dict[str, Any]:
    """
    Generate content inspired by current trending topics.

    Not low-quality trend-jacking — professional analysis based on trending subjects.
    """
    from agents.llm_client import get_llm_client

    topics_summary = "\n".join(
        f"- {t['term']}: \"{t['text'][:100]}...\" ({t['likes']} likes)"
        for t in trending_topics[:5]
    )

    system_prompt = """Generate a Bluesky post that naturally connects to current trading discussions.

Rules:
- Pick the most interesting trending topic and add your expert perspective
- Don't reference the original post directly — create standalone content inspired by the trend
- Under 300 characters
- No engagement bait
- End with something that invites genuine discussion
- End with: "\U0001f4ca Analysis by TradeIQ | Not financial advice"
"""

    user_prompt = f"""Currently trending on Bluesky trading community:
{topics_summary}

Persona: {persona_name}
Generate one post."""

    try:
        llm = get_llm_client()
        post = llm.simple_chat(system_prompt, user_prompt, max_tokens=150)
        return {
            "post_text": post.strip().strip('"'),
            "persona": persona_name,
            "inspired_by": trending_topics[0]["term"] if trending_topics else "",
            "status": "draft",
        }
    except Exception as exc:
        return {"error": str(exc)}
