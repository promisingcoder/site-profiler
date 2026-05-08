"""Strapi headless CMS detector — mostly an admin/edge fingerprint."""
from __future__ import annotations

import re

from ..base import (
    BodySubstrPattern,
    HeaderPattern,
    PatternDetector,
)


class Strapi(PatternDetector):
    name = "strapi"
    category = "framework"
    base_confidence = 0.9
    abstract = False
    matchers = (
        HeaderPattern("x-powered-by", re.compile(r"^Strapi", re.I)),
        BodySubstrPattern("strapi_jwt"),
    )
