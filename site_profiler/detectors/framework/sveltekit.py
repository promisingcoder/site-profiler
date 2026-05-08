"""SvelteKit (Svelte's app framework) detector. Distinct from plain Svelte —
SvelteKit always emits #svelte-announcer or data-sveltekit-* attributes."""
from __future__ import annotations

import re

from ..base import (
    BodySubstrPattern,
    HtmlAttrPattern,
    MetaGeneratorPattern,
    PatternDetector,
)


class SvelteKit(PatternDetector):
    name = "sveltekit"
    category = "framework"
    base_confidence = 0.9
    abstract = False
    matchers = (
        MetaGeneratorPattern(re.compile(r"^SvelteKit", re.I)),
        BodySubstrPattern('id="svelte-announcer"'),
        BodySubstrPattern("data-sveltekit-preload-data"),
        HtmlAttrPattern("data-sveltekit-"),
    )
