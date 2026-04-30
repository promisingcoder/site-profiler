"""Nuxt.js framework detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("framework")
def nuxt(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    body_lower = home.body_lower
    if "window.__nuxt__" in body_lower or "__nuxt__=" in body_lower:
        markers.append("window.__NUXT__ assignment")
    if 'id="__nuxt"' in body_lower:
        markers.append('<div id="__nuxt"> root')
    if "/_nuxt/" in body_lower:
        markers.append("/_nuxt/ asset paths")
    if "x-nuxt" in " ".join(home.headers_lc.keys()):
        for h in home.headers_lc:
            if h.startswith("x-nuxt"):
                markers.append(f"{h} header")

    if not markers:
        return None
    confidence = 0.95 if len(markers) >= 2 else 0.8
    return Evidence(name="nuxt", confidence=confidence, markers=markers)
