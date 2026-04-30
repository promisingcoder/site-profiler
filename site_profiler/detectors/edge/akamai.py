"""Akamai edge detector (covers AkamaiGHost, AkamaiNetStorage, EdgeStart, etc.)."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("edge")
def akamai(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    robots = pair.robots
    markers: list[str] = []

    server = home.header("server")
    s_lower = server.lower()
    if "akamai" in s_lower:
        markers.append(f"server: {server}")
    if home.header("x-akamai-transformed"):
        markers.append("x-akamai-transformed header")
    if home.header("akamai-grn"):
        markers.append("akamai-grn header")
    if home.header("akamai-request-bc"):
        markers.append("akamai-request-bc header")
    if home.header("x-akamai-request-id"):
        markers.append("x-akamai-request-id header")
    if home.header("akamai-true-ttl"):
        markers.append("akamai-true-ttl header")

    # Server-Timing: ak_p; desc=...
    for name, _params in home.server_timing:
        if name.lower() == "ak_p":
            markers.append("server-timing: ak_p")
            break

    aka_cookies = [
        c for c in home.set_cookie_names
        if c.startswith("AKA_")
        or c.startswith("akamai")
        or c.startswith("akainst")
        or c.startswith("akamref")
        or c.startswith("akavpau_")
        or c.startswith("ak_")
        or c == "TealeafAkaSid"
        or c.startswith("akaalb_")
        or c.startswith("wp_ak_")
    ]
    if aka_cookies:
        markers.append(f"akamai-family cookies: {aka_cookies}")

    # Robots-side hint (when home is blocked but robots set akamai cookies)
    robots_aka = [
        c for c in robots.set_cookie_names
        if c.startswith("AKA_") or c.startswith("akainst") or c.startswith("akamref") or c.startswith("akaalb_") or c.startswith("wp_ak_")
    ]
    if robots_aka and not markers:
        markers.append(f"robots.txt akamai cookies: {robots_aka}")

    if not markers:
        return None
    confidence = 0.99 if len(markers) >= 2 else 0.85
    return Evidence(name="akamai", confidence=confidence, markers=markers)
