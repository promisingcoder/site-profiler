"""AWS WAF Captcha detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("captcha")
def aws_waf_captcha(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for host in home.script_src_hosts:
        if "captcha.awswaf.com" in host or "token.awswaf.com" in host:
            markers.append(f"script host: {host}")

    body_lower = home.body_lower
    if "captchascript.rendercaptcha" in body_lower or "renderCaptcha".lower() in body_lower:
        markers.append("CaptchaScript.renderCaptcha body marker")

    waf_action = home.header("x-amzn-waf-action").lower()
    if waf_action == "captcha":
        markers.append("x-amzn-waf-action: captcha")

    if not markers:
        return None
    return Evidence(name="aws_waf_captcha", confidence=0.95, markers=markers, extra={"loaded": "true"})
