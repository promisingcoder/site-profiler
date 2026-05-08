"""Qwik / Qwik City detector. Captures version from the ``q:version``
attribute on the document root."""
from __future__ import annotations

import re

from ..base import (
    BodyRegexPattern,
    BodySubstrPattern,
    PatternDetector,
)


class Qwik(PatternDetector):
    name = "qwik"
    category = "framework"
    base_confidence = 0.9
    abstract = False
    matchers = (
        BodyRegexPattern(
            re.compile(r"q:version=\"([\d.]+(?:-\d+)?)\"", re.I),
            label="q:version attribute",
            capture_version=True,
        ),
        BodySubstrPattern("q:container"),
        BodySubstrPattern("q:base="),
    )
