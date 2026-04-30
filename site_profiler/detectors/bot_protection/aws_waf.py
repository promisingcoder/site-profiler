"""AWS WAF (with or without Captcha)."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("bot_protection")
def aws_waf(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    waf_action = home.header("x-amzn-waf-action").lower()
    if waf_action:
        markers.append(f"x-amzn-waf-action: {waf_action}")

    body_lower = home.body_lower
    if "awswafcookiedomainlist" in body_lower:
        markers.append("awsWafCookieDomainList body marker")
    if "awswafchallenge" in body_lower:
        markers.append("AwsWafChallenge body marker")
    if "awswafintegration" in body_lower:
        markers.append("AwsWafIntegration body marker")

    for host in home.script_src_hosts:
        if "awswaf.com" in host:
            markers.append(f"script host: {host}")

    if not markers:
        return None
    confidence = 0.95 if len(markers) >= 2 else 0.8
    extra = {"mode": "engaged"} if waf_action in ("captcha", "challenge", "block") else {"mode": "armed"}
    return Evidence(
        name="aws_waf",
        confidence=confidence,
        markers=markers,
        extra=extra,
    )
