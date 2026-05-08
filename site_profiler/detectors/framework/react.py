"""React vanilla detector. Note: most modern Next.js / Remix / Gatsby sites
will trigger React too — that's correct (React is a meta-tag layered under
the more specific framework). Strategy logic should rely on the more
specific framework's name when both fire.
"""
from __future__ import annotations

import re

from ..base import (
    BodyRegexPattern,
    BodySubstrPattern,
    PatternDetector,
)


class React(PatternDetector):
    name = "react"
    category = "framework"
    base_confidence = 0.7  # weaker by default — corroboration helps
    abstract = False
    matchers = (
        BodyRegexPattern(
            re.compile(r"react(?:-with-addons)?[.-]([\d]+\.[\d]+(?:\.[\d]+)?)[^/]*\.(?:min\.)?js", re.I),
            label="react.js loader URL",
            capture_version=True,
        ),
        BodySubstrPattern("data-reactroot"),
        BodySubstrPattern("data-react-helmet"),
        BodySubstrPattern("_reactrootcontainer"),
    )
