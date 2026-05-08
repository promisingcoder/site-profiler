"""Sanity headless CMS detector — usually identifiable from CDN asset hosts
on a frontend that consumes Sanity content."""
from __future__ import annotations

from ..base import (
    BodySubstrPattern,
    HeaderPrefixPattern,
    PatternDetector,
    ScriptHostPattern,
)


class Sanity(PatternDetector):
    name = "sanity"
    category = "framework"
    base_confidence = 0.85
    abstract = False
    matchers = (
        HeaderPrefixPattern("x-sanity-"),
        ScriptHostPattern("cdn.sanity.io"),
        BodySubstrPattern("cdn.sanity.io"),
        BodySubstrPattern("apicdn.sanity.io"),
    )
