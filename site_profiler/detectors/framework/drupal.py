"""Drupal CMS detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("framework")
def drupal(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    x_gen = home.header("x-generator").lower()
    if "drupal" in x_gen:
        markers.append(f"x-generator: {home.header('x-generator')}")

    for g in home.meta_generators:
        if "drupal" in g.lower():
            markers.append(f"meta generator: {g}")

    if home.header("x-drupal-dynamic-cache") or home.header("x-drupal-cache"):
        markers.append("x-drupal-cache header")

    body_lower = home.body_lower
    if "drupal.behaviors" in body_lower or 'drupalsettings' in body_lower:
        markers.append("Drupal.behaviors / drupalSettings JS")

    if not markers:
        return None
    confidence = 0.95 if len(markers) >= 2 else 0.85
    return Evidence(name="drupal", confidence=confidence, markers=markers)
