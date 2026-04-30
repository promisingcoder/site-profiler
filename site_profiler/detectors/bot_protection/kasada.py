"""Kasada bot protection."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("bot_protection")
def kasada(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for h in home.headers_lc:
        if h.startswith("x-kpsdk-"):
            markers.append(f"{h} header")

    if "kasada" in home.body_lower:
        markers.append("kasada body marker")

    if not markers:
        return None
    confidence = 0.9 if len(markers) >= 2 else 0.75
    return Evidence(name="kasada", confidence=confidence, markers=markers)
