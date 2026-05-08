"""Ruby on Rails detector."""
from __future__ import annotations

import re

from ..base import (
    BodyRegexPattern,
    BodySubstrPattern,
    CookiePattern,
    HeaderPattern,
    PatternDetector,
)


class Rails(PatternDetector):
    name = "rails"
    category = "framework"
    base_confidence = 0.85
    abstract = False
    matchers = (
        HeaderPattern("server", re.compile(r"mod_(?:rails|rack)", re.I)),
        HeaderPattern("x-powered-by", re.compile(r"mod_(?:rails|rack)", re.I)),
        CookiePattern(substr="_session_id"),
        BodySubstrPattern('name="csrf-param"'),
        BodyRegexPattern(
            re.compile(r"name=\"csrf-param\"\s+content=\"authenticity_token\"", re.I),
            label="csrf-param=authenticity_token meta",
        ),
    )
