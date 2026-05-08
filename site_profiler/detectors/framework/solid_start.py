"""SolidStart (Solid.js app framework) detector. Single strong marker:
``_$HY.init`` hydration boot call."""
from __future__ import annotations

from ..base import BodySubstrPattern, PatternDetector


class SolidStart(PatternDetector):
    name = "solid_start"
    category = "framework"
    base_confidence = 0.85
    abstract = False
    matchers = (
        BodySubstrPattern("_$hy.init"),
        BodySubstrPattern("_$hy.r["),
    )
