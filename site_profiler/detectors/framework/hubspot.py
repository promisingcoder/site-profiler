"""HubSpot CMS detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("framework")
def hubspot(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for h in home.headers_lc:
        if h.startswith("x-hs-"):
            markers.append(f"{h} header")

    for g in home.meta_generators:
        if "hubspot" in g.lower():
            markers.append(f"meta generator: {g}")

    for host in home.script_src_hosts:
        if "hubspot.com" in host or "hs-banner.com" in host or "hsappstatic.net" in host:
            markers.append(f"script host: {host}")

    if not markers:
        return None
    confidence = 0.95 if len(markers) >= 2 else 0.8
    return Evidence(name="hubspot", confidence=confidence, markers=markers)
