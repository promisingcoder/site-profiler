"""Cloudflare Turnstile detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("captcha")
def turnstile(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for src in home.script_srcs:
        s = src.lower()
        if "challenges.cloudflare.com/turnstile" in s or s.endswith("turnstile/v0/api.js"):
            markers.append(f"script src: {src}")
            break

    if not markers:
        return None
    return Evidence(name="turnstile", confidence=0.95, markers=markers, extra={"loaded": "true"})
