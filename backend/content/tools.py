"""
Content Generation Tools using DeepSeek LLM
Functions for Content Creator Agent
"""
from typing import Dict, Any, List, Optional
from agents.llm_client import get_llm_client
from agents.prompts import SYSTEM_PROMPT_CONTENT, MASTER_COMPLIANCE_RULES as COMPLIANCE_RULES
from .models import AIPersona, SocialPost
from datetime import datetime


def generate_draft(
    persona_id: str,
    topic: str,
    platform: str = "bluesky",
    max_length: int = 300
) -> Dict[str, Any]:
    """
    Generate a social media post draft using DeepSeek.
    
    Args:
        persona_id: AI Persona UUID
        topic: Topic or insight to post about
        platform: Platform (bluesky, twitter, etc.)
        max_length: Max character length
    
    Returns:
        Draft content dict
    """
    try:
        persona = AIPersona.objects.get(id=persona_id)
    except AIPersona.DoesNotExist:
        return {"error": "Persona not found"}
    
    llm = get_llm_client()
    
    # Build persona-specific prompt
    persona_prompt = persona.system_prompt or f"You are {persona.name}. {SYSTEM_PROMPT_CONTENT}"
    
    # Platform-specific constraints
    platform_rules = {
        "bluesky": "Bluesky post: concise, under 300 chars, insight-driven. Use emojis sparingly.",
        "twitter": "Twitter post: under 280 chars, engaging, use hashtags.",
        "linkedin": "LinkedIn post: professional, 300-500 chars, business-focused."
    }
    platform_rule = platform_rules.get(platform.lower(), platform_rules["bluesky"])
    
    prompt = f"""Generate a {platform} post about: {topic}

Persona: {persona.name}
Voice: {persona.personality_type or 'professional'}

Requirements:
- {platform_rule}
- {COMPLIANCE_RULES}
- Include factual data points
- End with: "📊 Analysis by TradeIQ | Not financial advice"
- No hype language: "moon", "rocket", "guaranteed", "easy money"

Generate ONLY the post content, no explanations."""
    
    try:
        content = llm.simple_chat(
            system_prompt=persona_prompt,
            user_message=prompt,
            temperature=0.7,
            max_tokens=150
        )
        
        # Ensure compliance disclaimer is present
        content_text = content.strip()
        if "📊 Analysis by TradeIQ" not in content_text:
            content_text += "\n\n📊 Analysis by TradeIQ | Not financial advice"
        
        # Truncate if too long
        if len(content_text) > max_length:
            content_text = content_text[:max_length-3] + "..."
        
        return {
            "content": content_text,
            "persona_id": persona_id,
            "persona_name": persona.name,
            "platform": platform,
            "length": len(content_text),
            "status": "draft"
        }
    except Exception as e:
        return {
            "error": str(e),
            "content": "",
            "status": "error"
        }


def generate_thread(
    persona_id: str,
    topic: str,
    num_posts: int = 3,
    platform: str = "bluesky"
) -> Dict[str, Any]:
    """
    Generate a thread (multiple connected posts) using DeepSeek.
    
    Args:
        persona_id: AI Persona UUID
        topic: Main topic
        num_posts: Number of posts in thread (max 5)
        platform: Platform
    
    Returns:
        Thread content dict
    """
    num_posts = min(num_posts, 5)  # Max 5 posts
    
    try:
        persona = AIPersona.objects.get(id=persona_id)
    except AIPersona.DoesNotExist:
        return {"error": "Persona not found"}
    
    llm = get_llm_client()
    
    persona_prompt = persona.system_prompt or f"You are {persona.name}. {SYSTEM_PROMPT_CONTENT}"
    
    prompt = f"""Generate a {platform} thread about: {topic}

Persona: {persona.name}
Number of posts: {num_posts}

Requirements:
- Each post under 300 chars
- Posts should flow logically (1/5, 2/5, etc. format)
- {COMPLIANCE_RULES}
- Include data points
- Last post ends with: "📊 Analysis by TradeIQ | Not financial advice"

Return JSON array with {num_posts} posts:
[
  {{"index": 1, "content": "..."}},
  {{"index": 2, "content": "..."}},
  ...
]"""
    
    try:
        response = llm.simple_chat(
            system_prompt=persona_prompt,
            user_message=prompt,
            temperature=0.7,
            max_tokens=800
        )
        
        # Parse JSON response
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        import json
        posts = json.loads(response_text)
        
        # Ensure compliance
        if posts and isinstance(posts, list):
            last_post = posts[-1]
            if isinstance(last_post, dict) and "📊 Analysis by TradeIQ" not in last_post.get("content", ""):
                last_post["content"] += "\n\n📊 Analysis by TradeIQ | Not financial advice"
        
        return {
            "posts": posts,
            "persona_id": persona_id,
            "persona_name": persona.name,
            "platform": platform,
            "num_posts": len(posts) if isinstance(posts, list) else 0,
            "status": "draft"
        }
    except Exception as e:
        return {
            "error": str(e),
            "posts": [],
            "status": "error"
        }


def format_for_platform(content: str, platform: str) -> str:
    """
    Format content for specific platform requirements.
    
    Args:
        content: Raw content
        platform: Target platform
    
    Returns:
        Formatted content
    """
    # Simple formatting - can be enhanced
    formatted = content.strip()
    
    if platform.lower() == "bluesky":
        # Ensure under 300 chars
        if len(formatted) > 300:
            formatted = formatted[:297] + "..."
    elif platform.lower() == "twitter":
        # Ensure under 280 chars
        if len(formatted) > 280:
            formatted = formatted[:277] + "..."
    
    return formatted
