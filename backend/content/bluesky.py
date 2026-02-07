# backend/content/bluesky.py - Appendix B
import re
from django.conf import settings


class BlueskyPublisher:
    """Publish trading content to Bluesky via AT Protocol."""

    def __init__(self):
        from atproto import Client
        self.client = Client()
        self.client.login(
            settings.BLUESKY_HANDLE,
            settings.BLUESKY_APP_PASSWORD,
        )

    def _build_facets(self, text: str) -> list:
        """
        Build AT Protocol facets for hashtags in text.
        Detects #hashtag patterns and creates proper facet objects.
        """
        facets = []
        for match in re.finditer(r'#(\w+)', text):
            tag = match.group(1)
            byte_start = len(text[:match.start()].encode('utf-8'))
            byte_end = len(text[:match.end()].encode('utf-8'))
            facets.append({
                "index": {"byteStart": byte_start, "byteEnd": byte_end},
                "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tag}],
            })
        return facets

    def _auto_hashtags(self, text: str) -> str:
        """Add TradeIQ hashtags if not already present and space allows."""
        tags = ["#TradeIQ", "#trading"]
        existing = set(re.findall(r'#\w+', text.lower()))
        to_add = [t for t in tags if t.lower() not in existing]
        suffix = " " + " ".join(to_add)
        if len(text) + len(suffix) <= 300:
            return text + suffix
        return text

    def post(self, text: str, external_url: str = None, external_title: str = None) -> dict:
        """
        Publish a single post (max 300 chars).
        Supports hashtag facets and optional link card embed.
        """
        text = self._auto_hashtags(text)
        facets = self._build_facets(text)

        kwargs = {"text": text}
        if facets:
            kwargs["facets"] = facets

        # External link card embed
        if external_url and external_title:
            kwargs["embed"] = {
                "$type": "app.bsky.embed.external",
                "external": {
                    "uri": external_url,
                    "title": external_title,
                    "description": "",
                },
            }

        response = self.client.send_post(**kwargs)
        return {
            "uri": response.uri,
            "cid": response.cid,
            "url": self._uri_to_url(response.uri),
        }

    def post_thread(self, posts: list) -> list:
        """Publish a thread (list of posts, each max 300 chars)."""
        results = []
        parent = None
        root = None

        for i, text in enumerate(posts):
            text = self._auto_hashtags(text) if i == 0 else text
            facets = self._build_facets(text)
            kwargs = {"text": text}
            if facets:
                kwargs["facets"] = facets

            if parent is None:
                response = self.client.send_post(**kwargs)
                root = {"uri": response.uri, "cid": response.cid}
                parent = root
            else:
                kwargs["reply_to"] = {"root": root, "parent": parent}
                response = self.client.send_post(**kwargs)
                parent = {"uri": response.uri, "cid": response.cid}

            results.append({
                "index": i,
                "uri": response.uri,
                "cid": response.cid,
                "url": self._uri_to_url(response.uri),
            })

        return results

    def search_posts(self, query: str, limit: int = 10) -> list:
        """
        Search Bluesky posts by keyword.
        Returns list of posts with author, text, and engagement.
        """
        try:
            resp = self.client.app.bsky.feed.search_posts(
                params={"q": query, "limit": min(limit, 25)}
            )
            results = []
            for post in resp.posts:
                results.append({
                    "text": post.record.text if hasattr(post.record, 'text') else "",
                    "author": post.author.handle if hasattr(post.author, 'handle') else "",
                    "author_name": post.author.display_name if hasattr(post.author, 'display_name') else "",
                    "like_count": post.like_count if hasattr(post, 'like_count') else 0,
                    "repost_count": post.repost_count if hasattr(post, 'repost_count') else 0,
                    "uri": post.uri,
                    "url": self._uri_to_url(post.uri),
                    "created_at": post.record.created_at if hasattr(post.record, 'created_at') else "",
                })
            return results
        except Exception as e:
            print(f"Bluesky search error: {e}")
            return []

    def _uri_to_url(self, uri: str) -> str:
        """Convert AT URI to web URL."""
        parts = uri.replace("at://", "").split("/")
        did = parts[0]
        post_id = parts[-1]
        return f"https://bsky.app/profile/{did}/post/{post_id}"
