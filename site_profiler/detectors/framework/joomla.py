"""Joomla CMS detector.

Captures version from generator meta or ``X-Content-Encoded-By`` header
(Joomla emits both).

Note on the absent md5-hex cookie matcher: Wappalyzer lists Joomla's
session cookie name as a 32-char hex string (md5 of the site secret).
That pattern matches *any* PHP framework that md5s its session name —
too noisy to use as a Joomla marker on its own. The header / generator /
URL pattern markers below are specific enough without it.
"""
from __future__ import annotations

import re

from ..base import (
    BodySubstrPattern,
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
        BodySubstrPattern("/components/com_"),
        BodySubstrPattern("?option=com_"),
    )
