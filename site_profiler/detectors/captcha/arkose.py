"""Arkose Labs / FunCaptcha detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("captcha")
def arkose(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for src in home.script_srcs:
        if "arkoselabs.com" in src.lower():
            markers.append(f"script src: {src}")
            break

    if "arkoselabs" in home.body_lower and not markers:
        # body reference (e.g., inline preload) — weaker signal
        markers.append("arkoselabs body reference")

    if not markers:
        return None
    confidence = 0.9 if any("script" in m for m in markers) else 0.7
    return Evidence(name="arkose", confidence=confidence, markers=markers, extra={"loaded": "true"})
