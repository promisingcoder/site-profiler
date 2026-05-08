"""Django (Python) detector. The ``csrfmiddlewaretoken`` form input is
distinctive — every POST form on a Django site renders it."""
from __future__ import annotations

import re

from ..base import (
    BodyRegexPattern,
    BodySubstrPattern,
    CookiePattern,
    PatternDetector,
)


class Django(PatternDetector):
    name = "django"
    category = "framework"
    base_confidence = 0.85
    abstract = False
    matchers = (
        CookiePattern(substr="csrftoken"),
        CookiePattern(substr="django_language"),
        CookiePattern(substr="sessionid"),
        BodySubstrPattern('name="csrfmiddlewaretoken"'),
        BodyRegexPattern(
            re.compile(r"powered by\s+<a[^>]+>django\s*([\d.]+)?</a>", re.I),
            label="Django footer attribution",
            capture_version=True,
        ),
    )
