"""GeeTest captcha detector.

Two major versions, distinguishable by network signature:
    - ``v3``: legacy slider/icon-click puzzle. Loader at ``static.geetest.com``,
      uses ``gt`` + ``challenge`` query params, ``initGeetest({...})`` API.
    - ``v4``: adaptive challenge ("OneTap" can be invisible). Loader at
      ``gcaptcha4.geetest.com`` (or ``static.geetest.com/v4/``), uses a
      single ``captcha_id`` parameter, ``initGeetest4({...})`` API.

Reference: https://docs.geetest.com — and the practical detection rule
(the ``gcaptcha4`` host vs ``initGeetest`` with two keys) appears in
multiple captcha-solver writeups; both form the basis of the variants here.
"""
from __future__ import annotations

from ...parse import FetchedPair
from ...schema import Variant
from ..base import BaseMatch, Detector, VariantProbe


class GeeTestV3(VariantProbe):
    name = "v3"
    label = "GeeTest v3 (slider/icon)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        body = pair.home.body_lower
        for src in pair.home.script_srcs:
            s = src.lower()
            if ("static.geetest.com/static/js/gt." in s
                or "static.geetest.com/static/js/geetest." in s
                or "static.geetest.com/static/products/gt/" in s):
                markers.append(f"v3 loader: {src}")
        if "initgeetest(" in body and "initgeetest4(" not in body:
            markers.append("initGeetest({...}) call (v3)")
        if "geetest_challenge" in body and "captcha_id" not in body:
            markers.append("gt+challenge params (v3)")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.9, markers=markers)


class GeeTestV4(VariantProbe):
    name = "v4"
    label = "GeeTest v4 (adaptive)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        body = pair.home.body_lower
        for src in pair.home.script_srcs:
            s = src.lower()
            if "gcaptcha4.geetest.com" in s or "/static/v4/" in s:
                markers.append(f"v4 loader: {src}")
        if "initgeetest4(" in body:
            markers.append("initGeetest4({...}) call (v4)")
        if 'captcha_id' in body and "geetest" in body:
            markers.append("captcha_id parameter (v4)")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.9, markers=markers)


class GeeTest(Detector):
    name = "geetest"
    category = "captcha"
    base_confidence = 0.9
    variants = (GeeTestV3, GeeTestV4)
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        markers: list[str] = []
        for src in pair.home.script_srcs:
            if "geetest.com" in src.lower():
                markers.append(f"script src: {src}")
                break
        if not markers and "geetest" in pair.home.body_lower:
            # generic body reference — weak
            markers.append("'geetest' body reference")
        if not markers:
            return BaseMatch()
        extra = {"loaded": "true"} if any("script src" in m for m in markers) else {"loaded": "false"}
        return BaseMatch(markers=markers, extra=extra)


geetest = GeeTest._runner  # type: ignore[attr-defined]
