"""hCaptcha detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("captcha")
def hcaptcha(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for src in home.script_srcs:
        if "hcaptcha.com" in src.lower():
            markers.append(f"script src: {src}")
            break
    if not markers and "hcaptcha-script" in home.body_lower:
        markers.append("hcaptcha-script body marker")

    if not markers:
        return None
    return Evidence(name="hcaptcha", confidence=0.95, markers=markers, extra={"loaded": "true"})
