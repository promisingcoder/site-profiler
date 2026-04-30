"""Ghost CMS detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("framework")
def ghost(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for g in home.meta_generators:
        if g.lower().startswith("ghost"):
            markers.append(f"meta generator: {g}")

    if home.header("x-ghost-cache-status"):
        markers.append("x-ghost-cache-status header")

    if not markers:
        return None
    confidence = 0.9
    return Evidence(name="ghost", confidence=confidence, markers=markers)
