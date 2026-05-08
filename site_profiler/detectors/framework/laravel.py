"""Laravel (PHP) detector. ``laravel_session`` cookie is the cleanest marker."""
from __future__ import annotations

import re

from ..base import (
    BodySubstrPattern,
    CookiePattern,
    PatternDetector,
)


class Laravel(PatternDetector):
    name = "laravel"
    category = "framework"
    base_confidence = 0.9
    abstract = False
    matchers = (
        CookiePattern(substr="laravel_session"),
        CookiePattern(substr="xsrf-token"),
        BodySubstrPattern('name="csrf-token"'),
    )
