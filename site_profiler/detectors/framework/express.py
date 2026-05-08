"""Express.js (Node) detector. Mostly a header / cookie signature."""
from __future__ import annotations

import re

from ..base import (
    CookiePattern,
    HeaderPattern,
    PatternDetector,
)


class Express(PatternDetector):
    name = "express"
    category = "framework"
    base_confidence = 0.9
    abstract = False
    matchers = (
        HeaderPattern("x-powered-by", re.compile(r"^Express(?:$|,)", re.I)),
        CookiePattern(substr="connect.sid"),
    )
