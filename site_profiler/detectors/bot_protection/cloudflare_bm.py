"""Cloudflare Bot Management — distinguishes 'armed' from 'engaged'."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("bot_protection")
def cloudflare_bm(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []
    extra: dict[str, str] = {}

    cf_mitigated = home.header("cf-mitigated").lower()
    if cf_mitigated == "challenge":
        markers.append("cf-mitigated: challenge (engaged)")
        extra["mode"] = "engaged"

    has_cf_bm = "__cf_bm" in home.set_cookie_names
    has_cfuvid = "_cfuvid" in home.set_cookie_names
    if has_cf_bm:
        markers.append("__cf_bm cookie")
    if has_cfuvid:
        markers.append("_cfuvid cookie")

    body_lower = home.body_lower
    if "/cdn-cgi/challenge-platform" in body_lower:
        markers.append("/cdn-cgi/challenge-platform script reference")
    if "_cf_chl_opt" in body_lower:
        markers.append("_cf_chl_opt body marker")

    if not markers:
        return None
    if "mode" not in extra:
        extra["mode"] = "armed_passive"
    confidence = 0.95 if cf_mitigated == "challenge" else 0.85
    return Evidence(
        name="cloudflare_bot_management",
        confidence=confidence,
        markers=markers,
        extra=extra,
    )
