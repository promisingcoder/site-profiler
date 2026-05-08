"""Framer Sites detector. Distinct from Framer Motion (the React animation
library) — Framer Sites is the no-code site builder, signaled by
``framerusercontent.com`` asset host."""
from __future__ import annotations

from ..base import (
    BodySubstrPattern,
    PatternDetector,
    ScriptHostPattern,
)


class Framer(PatternDetector):
    name = "framer"
    category = "framework"
    base_confidence = 0.95
    abstract = False
    matchers = (
        ScriptHostPattern("framerusercontent.com"),
        BodySubstrPattern("framerusercontent.com"),
        BodySubstrPattern("__framer_importfrompackage"),
    )
