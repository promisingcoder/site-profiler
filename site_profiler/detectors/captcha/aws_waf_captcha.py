"""AWS WAF Captcha detector.

AWS WAF can run a captcha action inline. The page surfaces it via:
    - script host ``captcha.awswaf.com`` (the loader),
    - script host ``token.awswaf.com`` (the JS-challenge token endpoint),
    - response header ``x-amzn-waf-action: captcha`` (definitive),
    - the body string ``CaptchaScript.renderCaptcha`` (the loader's render
      entry point — present in the inline boot stub).
"""
from __future__ import annotations

from ...parse import FetchedPair
from ..base import BaseMatch, Detector


class AwsWafCaptcha(Detector):
    name = "aws_waf_captcha"
    category = "captcha"
    base_confidence = 0.95
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        home = pair.home
        markers: list[str] = []

        for host in home.script_src_hosts:
            if "captcha.awswaf.com" in host or "token.awswaf.com" in host:
                markers.append(f"script host: {host}")

        body_lower = home.body_lower
        if "captchascript.rendercaptcha" in body_lower:
            markers.append("CaptchaScript.renderCaptcha body marker")

        waf_action = home.header("x-amzn-waf-action").lower()
        if waf_action == "captcha":
            markers.append("x-amzn-waf-action: captcha")

        if not markers:
            return BaseMatch()
        return BaseMatch(markers=markers, extra={"loaded": "true"})


aws_waf_captcha = AwsWafCaptcha._runner  # type: ignore[attr-defined]
