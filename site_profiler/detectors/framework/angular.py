"""Angular (modern, 2+) detector — distinct from AngularJS 1.x.

Captures version from the ``ng-version`` attribute applied to the root
component element by Angular at bootstrap.
"""
from __future__ import annotations

import re

from ..base import (
    BodyRegexPattern,
    BodySubstrPattern,
    PatternDetector,
)


class Angular(PatternDetector):
    name = "angular"
    category = "framework"
    base_confidence = 0.9
    abstract = False
    matchers = (
        BodyRegexPattern(
            re.compile(r"ng-version=\"([\d.]+)\"", re.I),
            label="ng-version attribute",
            capture_version=True,
        ),
        BodySubstrPattern("_nghost-"),
        BodySubstrPattern("_ngcontent-"),
    )


class AngularJS(PatternDetector):
    """AngularJS 1.x (legacy). Distinct framework, distinct upgrade path."""
    name = "angularjs"
    category = "framework"
    base_confidence = 0.85
    abstract = False
    matchers = (
        BodyRegexPattern(
            re.compile(r"ng-app=\"[^\"]*\"", re.I),
            label="ng-app attribute",
        ),
        BodyRegexPattern(
            re.compile(r"angular[.-]([\d]+\.[\d]+(?:\.[\d]+)?)[^/]*\.(?:min\.)?js", re.I),
            label="angular.js loader URL",
            capture_version=True,
        ),
        BodySubstrPattern("ng-controller="),
        BodySubstrPattern("ng-repeat="),
    )
