"""Vercel hosting/edge detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("edge")
def vercel(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    if home.header("server").lower() == "vercel":
        markers.append("server: Vercel")
    if home.header("x-vercel-id"):
        markers.append(f"x-vercel-id: {home.header('x-vercel-id')}")
    if home.header("x-vercel-cache"):
        markers.append(f"x-vercel-cache: {home.header('x-vercel-cache')}")

    # data-dpl-id="dpl_..." attribute on <html>
    dpl_id = home.html_attrs.get("data-dpl-id", "")
    if dpl_id and dpl_id.startswith("dpl_"):
        markers.append(f'data-dpl-id="{dpl_id}"')

    if not markers:
        return None
    confidence = 0.99 if len(markers) >= 2 else 0.85
    return Evidence(name="vercel", confidence=confidence, markers=markers)
