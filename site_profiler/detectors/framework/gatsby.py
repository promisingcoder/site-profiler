"""Gatsby framework detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("framework")
def gatsby(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for g in home.meta_generators:
        if "gatsby" in g.lower():
            markers.append(f"meta generator: {g}")

    body_lower = home.body_lower
    if 'id="___gatsby"' in body_lower or "window.___gatsby" in body_lower:
        markers.append("___gatsby root or global")
    if "/static/" in body_lower and "gatsby" in body_lower:
        # weak
        pass
    if any("gatsbyjs.com" in h or "gatsbyjs.org" in h for h in home.script_src_hosts):
        markers.append("gatsbyjs script host")

    if not markers:
        return None
    confidence = 0.9 if len(markers) >= 2 else 0.75
    return Evidence(name="gatsby", confidence=confidence, markers=markers)
