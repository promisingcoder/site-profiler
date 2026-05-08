"""Squarespace site builder detector."""
from __future__ import annotations

import re

from ..base import (
    BodySubstrPattern,
    HeaderPattern,
    PatternDetector,
)


class Squarespace(PatternDetector):
    name = "squarespace"
    category = "framework"
    base_confidence = 0.95
    abstract = False
    matchers = (
        HeaderPattern("server", re.compile(r"^Squarespace$", re.I)),
        BodySubstrPattern("static.squarespace.com"),
        BodySubstrPattern("squarespace_context"),
        BodySubstrPattern("squarespace.com/universal/scripts-compressed"),
    )
