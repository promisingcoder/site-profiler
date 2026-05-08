"""Vue.js (vanilla) detector — for sites using Vue *without* Nuxt.

Nuxt sites will trigger both Vue and Nuxt detectors; that's expected.
"""
from __future__ import annotations

import re

from ..base import (
    BodyRegexPattern,
    BodySubstrPattern,
    PatternDetector,
)


class Vue(PatternDetector):
    name = "vue"
    category = "framework"
    base_confidence = 0.8
    abstract = False
    matchers = (
        BodyRegexPattern(
            re.compile(r"vue[.-]([\d]+\.[\d]+(?:\.[\d]+)?)[^/]*\.(?:min\.)?js", re.I),
            label="vue.js loader URL",
            capture_version=True,
        ),
        BodyRegexPattern(
            re.compile(r"<[^>]+\sdata-v-[a-f0-9]{6,}", re.I),
            label="data-v-* scoped-style attribute",
        ),
        BodySubstrPattern("data-v-app"),
        BodySubstrPattern("__vue__"),
    )
