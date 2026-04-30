"""Fastly edge detector. Differentiates from generic Varnish via x-served-by POP names."""
from __future__ import annotations

import re

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence

# Fastly POP names like "cache-lin1730055-LIN" or "cache-par-lfpb1150054-PAR"
FASTLY_POP_RE = re.compile(r"cache-[a-z]+\d*[a-z]*\d*-[A-Z]{3}", re.IGNORECASE)


@register("edge")
def fastly(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    if home.header("x-fastly"):
        markers.append(f"x-fastly: {home.header('x-fastly')}")
    if home.header("x-fastly-cache-status"):
        markers.append(f"x-fastly-cache-status: {home.header('x-fastly-cache-status')}")
    if home.header("x-fastly-request-id"):
        markers.append("x-fastly-request-id header")

    served_by = home.header("x-served-by")
    if served_by and FASTLY_POP_RE.search(served_by):
        markers.append(f"x-served-by: {served_by}")

    via = home.header("via").lower()
    has_varnish = "varnish" in via
    if has_varnish and (markers or home.header("x-served-by") or home.header("x-timer")):
        markers.append(f"via: {home.header('via')}")
    if home.header("x-timer") and (has_varnish or markers):
        markers.append("x-timer header")

    if not markers:
        return None
    confidence = 0.95 if len(markers) >= 2 else 0.7
    return Evidence(name="fastly", confidence=confidence, markers=markers)
