"""First-party / homegrown bot protection (Reddit, TikTok internal WAF, custom interstitials)."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("bot_protection")
def first_party(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []
    name = "first_party_interstitial"

    body_lower = home.body_lower
    title_lower = home.title.lower()
    server = home.header("server").lower()

    # Reddit-style: server: snooserv, "please wait for verification" interstitial
    if "snooserv" in server or "please wait for verification" in title_lower:
        markers.append(f"server: {home.header('server')}" if server else "interstitial title")
        if "please wait for verification" in body_lower or "please wait for verification" in title_lower:
            markers.append("'please wait for verification' interstitial")
        name = "reddit_interstitial"

    # TikTok WAF: _wafchallengeid, slardar, captchami
    if "_wafchallengeid" in body_lower or "waforiginalreid" in body_lower:
        markers.append("_wafchallengeid / waforiginalreid body markers")
        name = "tiktok_internal_waf"
    if "slardar" in body_lower and ("waf" in body_lower or "captchami" in body_lower):
        markers.append("slardar + waf/captchami markers")
        if name == "first_party_interstitial":
            name = "tiktok_internal_waf"

    if not markers:
        return None
    return Evidence(name=name, confidence=0.85, markers=markers)
