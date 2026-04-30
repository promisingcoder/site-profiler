"""Netlify hosting/edge detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("edge")
def netlify(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    if "netlify" in home.header("server").lower():
        markers.append(f"server: {home.header('server')}")
    if home.header("x-nf-request-id"):
        markers.append("x-nf-request-id header")

    if not markers:
        return None
    confidence = 0.95 if len(markers) >= 2 else 0.85
    return Evidence(name="netlify", confidence=confidence, markers=markers)
