"""PerimeterX / HUMAN bot protection."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence

PX_COOKIES = ("_pxhd", "_px3", "_pxvid", "_pxhd_cf", "_pxff_cc")


@register("bot_protection")
def perimeterx(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    cookie_hits = [c for c in PX_COOKIES if c in home.set_cookie_names]
    if cookie_hits:
        markers.append(f"perimeterx cookies: {cookie_hits}")

    body_lower = home.body_lower
    if "px-cloud.net" in body_lower:
        markers.append("px-cloud.net script")
    if "_pxappid" in body_lower:
        markers.append("_pxAppId body marker")
    if "client.px-cdn.net" in body_lower:
        markers.append("client.px-cdn.net script")
    if "perimeterx" in body_lower:
        markers.append("perimeterx body marker")

    for host in home.script_src_hosts:
        if "px-cloud.net" in host or "px-cdn.net" in host or "perimeterx.net" in host:
            markers.append(f"script host: {host}")

    if not markers:
        return None
    confidence = 0.95 if len(markers) >= 2 else 0.8
    return Evidence(name="perimeterx", confidence=confidence, markers=markers)
