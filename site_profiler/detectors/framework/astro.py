"""Astro detector."""
from __future__ import annotations

import re

from ..base import (
    BodySubstrPattern,
    MetaGeneratorPattern,
    PatternDetector,
    ScriptSrcPattern,
)


class Astro(PatternDetector):
    name = "astro"
    category = "framework"
    base_confidence = 0.85
    abstract = False
    matchers = (
        MetaGeneratorPattern(
            re.compile(r"^Astro(?:\s+v?([\d.]+))?", re.I),
            capture_version=True,
        ),
        BodySubstrPattern("astro-island"),
        BodySubstrPattern("astro-static-slot"),
        ScriptSrcPattern("/_astro/"),
    )
