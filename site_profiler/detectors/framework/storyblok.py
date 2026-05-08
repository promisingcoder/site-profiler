"""Storyblok headless CMS detector. Usually identified by CDN asset host
``a.storyblok.com`` and ``StoryblokBridge`` JS global."""
from __future__ import annotations

from ..base import (
    BodySubstrPattern,
    PatternDetector,
)


class Storyblok(PatternDetector):
    name = "storyblok"
    category = "framework"
    base_confidence = 0.85
    abstract = False
    matchers = (
        BodySubstrPattern("a.storyblok.com"),
        BodySubstrPattern("storyblokbridge"),
        BodySubstrPattern("storyblokregisterevent"),
    )
