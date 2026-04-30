"""Cloudflare edge detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("edge")
def cloudflare(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    server = home.header("server").lower()
    if "cloudflare" in server:
        markers.append(f"server: {home.header('server')}")

    if home.header("cf-ray"):
        markers.append(f"cf-ray: {home.header('cf-ray')}")
    if home.header("cf-cache-status"):
        markers.append(f"cf-cache-status: {home.header('cf-cache-status')}")
    if home.header("cf-edge-cache"):
        markers.append(f"cf-edge-cache: {home.header('cf-edge-cache')}")
    if home.header("cf-apo-via"):
        markers.append(f"cf-apo-via: {home.header('cf-apo-via')}")
    if home.header("cf-mitigated"):
        markers.append(f"cf-mitigated: {home.header('cf-mitigated')}")

    for cookie in ("__cf_bm", "_cfuvid", "cf_clearance"):
        if cookie in home.set_cookie_names:
            markers.append(f"{cookie} cookie")

    if not markers:
        return None
    confidence = 0.99 if len(markers) >= 2 else 0.85
    return Evidence(name="cloudflare", confidence=confidence, markers=markers)
