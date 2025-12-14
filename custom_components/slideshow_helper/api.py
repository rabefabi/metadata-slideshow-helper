from __future__ import annotations

from .scanner import ImageMeta


class FeedFormatter:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url

    def to_urls(self, items: list[ImageMeta]) -> list[str]:
        # In HA, consider media proxy; for now, return raw paths
        return [it.path for it in items]
