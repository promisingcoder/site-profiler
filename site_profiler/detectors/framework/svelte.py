"""Svelte runtime detector (vanilla, non-SvelteKit). The hashed
``data-svelte-h`` attribute is the strongest cross-version marker."""
from __future__ import annotations

import re

from ..base import (
    BodyRegexPattern,
    BodySubstrPattern,
    PatternDetector,
)


class Svelte(PatternDetector):
    name = "svelte"
    category = "framework"
    base_confidence = 0.8
    abstract = False
    matchers = (
        BodyRegexPattern(
            re.compile(r"data-svelte-h=\"svelte-[a-z0-9]{6,}\"", re.I),
            label="data-svelte-h hash attribute",
        ),
        BodySubstrPattern('class="svelte-'),
    )
