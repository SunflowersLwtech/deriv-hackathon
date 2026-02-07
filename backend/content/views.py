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
                results = publisher.post_thread(content)
            else:
                results = publisher.post(content)

            return Response({
                "success": True,
                "status": "published",
                "platform": "bluesky",
                "uri": results.get("uri") if isinstance(results, dict) else str(results),
            })
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e),
            }, status=500)
