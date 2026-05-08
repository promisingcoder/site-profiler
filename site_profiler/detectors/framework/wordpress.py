"""WordPress detector. Robust to enterprise variants that strip generator meta.

Captures the WP version off ``<meta name="generator" content="WordPress X.Y.Z">``
when present (sites running WP-Hardening or W3 Total Cache may strip it,
leaving us with markers but no version).
"""
from __future__ import annotations

import re

from ...parse import FetchedPair
from ..base import BaseMatch, Detector

_GENERATOR_VERSION = re.compile(r"^wordpress(?:\s+([\d.]+))?", re.I)


class WordPress(Detector):
    name = "wordpress"
    category = "framework"
    base_confidence = 0.8
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        home = pair.home
        robots = pair.robots
        markers: list[str] = []
        version: str | None = None

        link_h = home.header("link")
        if "api.w.org" in link_h.lower():
            markers.append("Link: rel=https://api.w.org/")

        cf_edge = home.header("cf-edge-cache").lower()
        if "platform=wordpress" in cf_edge:
            markers.append(f"cf-edge-cache: {home.header('cf-edge-cache')}")

        for g in home.meta_generators:
            gl = g.lower()
            if "wordpress" in gl or "aioseo" in gl or "yoast" in gl:
                markers.append(f"meta generator: {g}")
                m = _GENERATOR_VERSION.search(g)
                if m and m.group(1) and version is None:
                    version = m.group(1)

        powered_by = home.header("x-powered-by").lower()
        if "wordpress vip" in powered_by:
            markers.append(f"x-powered-by: {home.header('x-powered-by')}")
        if home.header("x-pingback"):
            markers.append("x-pingback header")

        body_lower = home.body_lower
        if body_lower.count("wp-content/") >= 5:
            markers.append(f"wp-content/ paths in body (~{body_lower.count('wp-content/')} hits)")
        if body_lower.count("wp-includes/") >= 3:
            markers.append("wp-includes/ paths in body")
        if "wp-block-" in body_lower:
            markers.append("wp-block-* class names")

        for k, vals in pair.robots_parsed.nonstandard_directives.items():
            for v in vals:
                if "wp-json" in v.lower():
                    markers.append(f"robots.txt {k}: {v}")
                    break

        cookies = home.set_cookie_names + robots.set_cookie_names
        if any(c.startswith("wp_ak_") for c in cookies):
            markers.append("wp_ak_* cookies (WP behind Akamai)")
        if any(c.startswith("wordpress_logged_in_") for c in cookies):
            markers.append("wordpress_logged_in_* cookie")

        if not markers:
            return BaseMatch()
        return BaseMatch(markers=markers, version=version)


wordpress = WordPress._runner  # type: ignore[attr-defined]
