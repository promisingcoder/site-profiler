"""Joomla CMS detector. Captures version from generator meta or
``X-Content-Encoded-By`` header (Joomla emits both)."""
from __future__ import annotations

import re

from ..base import (
    BodySubstrPattern,
    CookiePattern,
    HeaderPattern,
    MetaGeneratorPattern,
    PatternDetector,
)


class Joomla(PatternDetector):
    name = "joomla"
    category = "framework"
    base_confidence = 0.85
    abstract = False
    matchers = (
        HeaderPattern(
            "x-content-encoded-by",
            re.compile(r"Joomla!?\s*([\d.]+)?", re.I),
            capture_version=True,
        ),
        MetaGeneratorPattern(
            re.compile(r"^Joomla!?(?:\s+([\d.]+))?", re.I),
            capture_version=True,
        ),
        CookiePattern(pattern=re.compile(r"^[a-f0-9]{32}$")),  # Joomla session cookie names are hex md5
        BodySubstrPattern("/components/com_"),
        BodySubstrPattern("?option=com_"),
    )
