"""Drupal CMS detector. Captures the major-version when ``X-Generator``
or ``<meta name="generator">`` carries it (Drupal 8/9/10 do; Drupal 7
sometimes does)."""
from __future__ import annotations

import re

from ...parse import FetchedPair
from ..base import BaseMatch, Detector

_GENERATOR_VERSION = re.compile(r"drupal\s+([\d.]+)", re.I)


class Drupal(Detector):
    name = "drupal"
    category = "framework"
    base_confidence = 0.85
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        home = pair.home
        markers: list[str] = []
        version: str | None = None

        x_gen = home.header("x-generator")
        if "drupal" in x_gen.lower():
            markers.append(f"x-generator: {x_gen}")
            m = _GENERATOR_VERSION.search(x_gen)
            if m:
                version = m.group(1)

        for g in home.meta_generators:
            if "drupal" in g.lower():
                markers.append(f"meta generator: {g}")
                if version is None:
                    m = _GENERATOR_VERSION.search(g)
                    if m:
                        version = m.group(1)

        if home.header("x-drupal-dynamic-cache") or home.header("x-drupal-cache"):
            markers.append("x-drupal-cache header")

        body_lower = home.body_lower
        if "drupal.behaviors" in body_lower or "drupalsettings" in body_lower:
            markers.append("Drupal.behaviors / drupalSettings JS")

        # Drupal session cookie SESS<32 hex chars>
        for c in home.set_cookie_names:
            if c.startswith("SESS") and len(c) == 36:
                markers.append(f"SESS<32 hex> cookie: {c}")
                break

        if not markers:
            return BaseMatch()
        return BaseMatch(markers=markers, version=version)


drupal = Drupal._runner  # type: ignore[attr-defined]
