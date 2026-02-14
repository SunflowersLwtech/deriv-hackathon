from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import AIPersona, SocialPost
from .serializers import AIPersonaSerializer, SocialPostSerializer
from .tools import generate_draft, generate_thread
from tradeiq.permissions import IsAuthenticatedOrReadOnly


class AIPersonaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIPersona.objects.all()
    serializer_class = AIPersonaSerializer


class SocialPostViewSet(viewsets.ModelViewSet):
    queryset = SocialPost.objects.all()
    serializer_class = SocialPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class GenerateContentView(APIView):
    """
    POST /api/content/generate/
    {
        "insight": "EUR/USD rose 0.5% on Fed comments",
        "platform": "bluesky_post" | "bluesky_thread",
        "persona_id": "uuid" (optional, defaults to Calm Analyst)
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        insight = request.data.get("insight", "")
        platform = request.data.get("platform", "bluesky_post")
        persona_id = request.data.get("persona_id")

        if not insight:
            return Response({"error": "insight is required"}, status=400)

        # Default to Calm Analyst persona
        if not persona_id:
            calm = AIPersona.objects.first()
            if calm:
                persona_id = str(calm.id)
            else:
                return Response({"error": "No personas configured"}, status=404)

        if platform == "bluesky_thread":
            result = generate_thread(
                persona_id=persona_id,
                topic=insight,
                num_posts=3,
                platform="bluesky"
            )
            content = "\n\n---\n\n".join(
                [p.get("content", "") for p in result.get("posts", [])]
            ) if result.get("posts") else ""
        else:
            result = generate_draft(
                persona_id=persona_id,
                topic=insight,
                platform="bluesky",
                max_length=300
            )
            content = result.get("content", "")

        return Response({
            "content": content,
            "platform": platform,
            "persona": result.get("persona_name", ""),
            "disclaimer": "This is AI-generated analysis, not financial advice.",
            "status": result.get("status", "draft"),
        })


class PublishToBlueskyView(APIView):
    """Appendix B - POST content to Bluesky (single or thread)."""
    permission_classes = [AllowAny]

    @staticmethod
    def _normalize_thread_posts(content):
        """
        Normalize thread payload into list[str].
        Accepts either:
        - list of posts
        - string joined by "\\n\\n---\\n\\n"
        - plain string (treated as single post)
        """
        if isinstance(content, list):
            posts = []
            for item in content:
                if isinstance(item, dict):
                    value = str(item.get("content", "")).strip()
                else:
                    value = str(item).strip()
                if value:
                    posts.append(value)
        elif isinstance(content, str):
            raw = content.strip()
            if not raw:
                posts = []
            elif "\n\n---\n\n" in raw:
                posts = [part.strip() for part in raw.split("\n\n---\n\n") if part.strip()]
            else:
                posts = [raw]
        else:
            posts = []

        # Bluesky hard limit per post
        return [post[:300] for post in posts][:5]

    def post(self, request):
        content = request.data.get("content")
        post_id = request.data.get("post_id")
        post_type = request.data.get("type", "single")

        # If post_id provided, get content from DB
        if post_id and not content:
            try:
                post = SocialPost.objects.get(id=post_id)
                content = post.content
            except SocialPost.DoesNotExist:
                return Response({"error": "Post not found"}, status=404)

        if not content:
            return Response({"error": "content is required"}, status=400)

        try:
            from .bluesky import BlueskyPublisher
        except ImportError:
            return Response({"error": "atproto not installed"}, status=503)

        publisher = BlueskyPublisher()

        try:
            if post_type == "thread":
                thread_posts = self._normalize_thread_posts(content)
                if not thread_posts:
                    return Response({"error": "thread content is empty"}, status=400)
                results = publisher.post_thread(thread_posts)
            else:
                if isinstance(content, list):
                    content = "\n\n".join(str(item).strip() for item in content if str(item).strip())
                if not isinstance(content, str):
                    return Response({"error": "content must be a string for single post"}, status=400)
                results = publisher.post(content)

            return Response({
                "success": True,
                "status": "published",
                "platform": "bluesky",
                "uri": results.get("uri") if isinstance(results, dict) else None,
                "results": results if isinstance(results, list) else None,
            })
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e),
            }, status=500)


class BlueskyCommunityView(APIView):
    """Bluesky community interaction endpoint."""
    permission_classes = [AllowAny]

    def get(self, request):
        """GET: Discover trending topics."""
        from content.community import discover_trending_topics
        topics = discover_trending_topics(limit=10)
        return Response({"topics": topics})

    def post(self, request):
        """POST: Generate trend content or reply draft."""
        action = request.data.get("action", "trend_content")
        persona = request.data.get("persona", "calm_analyst")

        if action == "trend_content":
            from content.community import discover_trending_topics, generate_trend_content
            topics = discover_trending_topics(limit=5)
            result = generate_trend_content(topics, persona)
            return Response(result)

        elif action == "reply_draft":
            from content.community import generate_reply_draft
            original = request.data.get("original_post", {})
            result = generate_reply_draft(original, persona)
            return Response(result)

        return Response({"error": "Unknown action"}, status=400)


class MultiPersonaView(APIView):
    """Multi-persona collaborative content endpoint."""
    permission_classes = [AllowAny]

    def post(self, request):
        from content.multi_persona import generate_multi_persona_content
        from dataclasses import asdict
        event = request.data.get("event", {})
        result = generate_multi_persona_content(event)
        return Response(asdict(result))


class BlueskySearchView(APIView):
    """
    GET /api/content/bluesky-search/?q=EUR+USD&limit=10
    Search Bluesky posts for social sentiment.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "")
        limit = int(request.query_params.get("limit", 10))
        if not query:
            return Response({"error": "q parameter is required"}, status=400)
        try:
            from .bluesky import BlueskyPublisher
            publisher = BlueskyPublisher()
            posts = publisher.search_posts(query, limit=limit)
            return Response({"query": query, "posts": posts, "count": len(posts)})
        except Exception as e:
            return Response({"error": str(e), "posts": []}, status=500)
