"""Contentful headless CMS detector — usually identified by CDN asset hosts
(``ctfassets.net``, ``images.ctfassets.net``)."""
from __future__ import annotations

import re

from ..base import (
    BodyRegexPattern,
    BodySubstrPattern,
    HeaderPattern,
    PatternDetector,
    ScriptHostPattern,
)


class Contentful(PatternDetector):
    name = "contentful"
    category = "framework"
    base_confidence = 0.85
    abstract = False
    matchers = (
        HeaderPattern("x-contentful-request-id"),
        HeaderPattern("server", re.compile(r"^Contentful Images API$", re.I)),
        ScriptHostPattern("ctfassets.net"),
        BodyRegexPattern(
            re.compile(r"https?://[^/\"']+\.(?:ct?fassets\.net|contentful\.com)", re.I),
            label="ctfassets.net / contentful.com asset URL",
        ),
        BodySubstrPattern("api.contentful.com"),
    )
