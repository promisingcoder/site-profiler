"""GeeTest captcha detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("captcha")
def geetest(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for src in home.script_srcs:
        if "geetest.com" in src.lower():
            markers.append(f"script src: {src}")
            break

    if not markers:
        return None
    return Evidence(name="geetest", confidence=0.9, markers=markers, extra={"loaded": "true"})
