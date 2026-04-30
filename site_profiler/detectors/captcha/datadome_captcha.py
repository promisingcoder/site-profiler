"""DataDome captcha detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("captcha")
def datadome_captcha(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    body_lower = home.body_lower
    if "datadomeclientkey" in body_lower:
        markers.append("datadomeClientKey body marker")
    if "datadome-container" in body_lower:
        markers.append("datadome-container element")
    if "captcha-delivery.com" in body_lower:
        markers.append("captcha-delivery.com script reference")
    if home.title.strip().lower() in {"bot or not?", "blocked"} and "datadome" in body_lower:
        markers.append(f"title '{home.title.strip()}' + datadome reference")

    if not markers:
        return None
    return Evidence(name="datadome_captcha", confidence=0.95, markers=markers, extra={"loaded": "true"})
