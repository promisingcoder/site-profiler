"""Akamai Bot Manager — _abck + bm_* cookie family is the canonical signal."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence

BM_COOKIES = ("_abck", "bm_sz", "bm_so", "bm_ss", "bm_s", "bm_mi", "bm_lso")


@register("bot_protection")
def akamai_bm(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    bm_hits = [c for c in BM_COOKIES if c in home.set_cookie_names]
    if bm_hits:
        markers.append(f"akamai bm cookies: {bm_hits}")

    body_lower = home.body_lower
    if "_abck" in body_lower and "akamai" in body_lower:
        markers.append("_abck/akamai body markers")

    if not markers:
        return None
    extra = {"mode": "armed_passive"}
    if (home.status or 0) >= 400:
        extra["mode"] = "engaged"
    confidence = 0.95 if len(bm_hits) >= 2 else 0.8
    return Evidence(
        name="akamai_bot_manager",
        confidence=confidence,
        markers=markers,
        extra=extra,
    )
