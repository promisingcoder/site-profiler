"""DataDome bot protection."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("bot_protection")
def datadome(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    if home.header("x-dd-b"):
        markers.append("x-dd-b header")
    if home.header("x-datadome-timer"):
        markers.append("x-datadome-timer header")
    if "datadome" in home.set_cookie_names:
        markers.append("datadome cookie")

    body_lower = home.body_lower
    if "datadomeclientkey" in body_lower:
        markers.append("datadomeClientKey in body")
    if "datadome-container" in body_lower:
        markers.append("datadome-container in body")
    if "captcha-delivery.com" in body_lower:
        markers.append("captcha-delivery.com reference")

    if not markers:
        return None
    confidence = 0.95 if len(markers) >= 2 else 0.8
    extra = {"mode": "armed_passive"}
    if any("datadomeclientkey" in m or "datadome-container" in m for m in markers):
        extra["mode"] = "engaged"
    return Evidence(
        name="datadome",
        confidence=confidence,
        markers=markers,
        extra=extra,
    )
