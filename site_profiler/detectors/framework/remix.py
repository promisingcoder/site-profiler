"""Remix (now part of React Router v7) detector.

Distinct globals — ``__remixContext``, ``__remixRouter``,
``__remixRouteModules`` — appear inline in the rendered document.
"""
from __future__ import annotations

from ..base import BodySubstrPattern, PatternDetector


class Remix(PatternDetector):
    name = "remix"
    category = "framework"
    base_confidence = 0.9
    abstract = False
    matchers = (
        BodySubstrPattern("window.__remixcontext"),
        BodySubstrPattern("window.__remixroutemodules"),
        BodySubstrPattern("window.__remixrouter"),
    )
