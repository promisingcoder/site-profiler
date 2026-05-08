"""hCaptcha detector.

Variants distinguished:
    - ``standard``: visible image-grid widget (``class="h-captcha"``).
    - ``invisible``: ``data-size="invisible"`` widget triggered programmatically.
    - ``enterprise``: loader URL contains ``?endpoint=enterprise`` and/or
      ``hcaptcha.execute`` is paired with enterprise-only configuration.
"""
from __future__ import annotations

from ...parse import FetchedPair
from ...schema import Variant
from ..base import BaseMatch, Detector, VariantProbe


class HcaptchaStandard(VariantProbe):
    name = "standard"
    label = "hCaptcha (visible)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        body = pair.home.body_lower
        # If invisible markers are present, this is *not* the visible variant.
        if 'data-size="invisible"' in body or "hcaptcha.execute(" in body:
            return None
        markers: list[str] = []
        if 'class="h-captcha"' in body or "class='h-captcha'" in body:
            markers.append("h-captcha widget element")
        if 'data-sitekey=' in body and "h-captcha" in body:
            markers.append("h-captcha + data-sitekey (visible)")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.95, markers=markers)


class HcaptchaInvisible(VariantProbe):
    name = "invisible"
    label = "hCaptcha (invisible)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        body = pair.home.body_lower
        markers: list[str] = []
        if 'data-size="invisible"' in body and "h-captcha" in body:
            markers.append('data-size="invisible" on h-captcha element')
        if "hcaptcha.execute(" in body and "h-captcha" in body:
            markers.append("hcaptcha.execute(...) call")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.9, markers=markers)


class HcaptchaEnterprise(VariantProbe):
    name = "enterprise"
    label = "hCaptcha Enterprise"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        for src in pair.home.script_srcs:
            s = src.lower()
            if "hcaptcha.com" in s and "endpoint=enterprise" in s:
                markers.append(f"enterprise loader: {src}")
        body = pair.home.body_lower
        if "hcaptcha.com/1/api.js?endpoint=enterprise" in body:
            markers.append("?endpoint=enterprise in body")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.95, markers=markers)


class Hcaptcha(Detector):
    name = "hcaptcha"
    category = "captcha"
    base_confidence = 0.95
    variants = (HcaptchaStandard, HcaptchaInvisible, HcaptchaEnterprise)
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        markers: list[str] = []
        for src in pair.home.script_srcs:
            if "hcaptcha.com" in src.lower():
                markers.append(f"script src: {src}")
                break
        body = pair.home.body_lower
        if not markers and "hcaptcha-script" in body:
            markers.append("hcaptcha-script body marker")
        if not markers and "h-captcha" in body and "data-sitekey" in body:
            markers.append("h-captcha widget element")
        if not markers:
            return BaseMatch()
        extra = {"loaded": "true"} if any("script src" in m for m in markers) else {"loaded": "false"}
        return BaseMatch(markers=markers, extra=extra)


hcaptcha = Hcaptcha._runner  # type: ignore[attr-defined]
