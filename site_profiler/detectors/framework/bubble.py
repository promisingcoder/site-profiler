"""Bubble.io (no-code) detector. Multiple x-bubble-* headers + bubble_*
globals in body."""
from __future__ import annotations

from ..base import (
    BodySubstrPattern,
    HeaderPrefixPattern,
    PatternDetector,
)


class Bubble(PatternDetector):
    name = "bubble"
    category = "framework"
    base_confidence = 0.95
    abstract = False
    matchers = (
        HeaderPrefixPattern("x-bubble-"),
        BodySubstrPattern("bubble_environment"),
        BodySubstrPattern("bubble_version"),
        BodySubstrPattern("_bubble_page_load_data"),
    )
