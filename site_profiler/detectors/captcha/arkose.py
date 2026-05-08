"""Arkose Labs / FunCaptcha detector.

Arkose Labs ships under two brand names you'll see in markup:
    - ``client-api.arkoselabs.com`` (modern host)
    - ``funcaptcha.com`` / ``api.funcaptcha.com`` (legacy alias)

The challenge surface is a 3D rotation puzzle inside an iframe; the iframe
URL contains the public key. We don't try to fingerprint the *challenge*
form (rotation, image, audio) from a server response — Arkose decides at
runtime — so there is currently a single ``standard`` variant, kept for
shape parity with other captcha detectors and so future variants
(rotation-only / hybrid / etc.) can be added without breaking callers.
"""
from __future__ import annotations

from ...parse import FetchedPair
from ...schema import Variant
from ..base import BaseMatch, Detector, VariantProbe


class ArkoseFunCaptcha(VariantProbe):
    name = "funcaptcha"
    label = "Arkose Labs FunCaptcha"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        for src in pair.home.script_srcs:
            s = src.lower()
            if "client-api.arkoselabs.com" in s:
                markers.append(f"script src: {src}")
            elif "funcaptcha.com" in s:
                markers.append(f"funcaptcha legacy host: {src}")
        body = pair.home.body_lower
        if "data-pkey=" in body and "arkoselabs" in body:
            markers.append("data-pkey + arkoselabs body marker")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.9, markers=markers)


class Arkose(Detector):
    name = "arkose"
    category = "captcha"
    base_confidence = 0.9
    variants = (ArkoseFunCaptcha,)
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        markers: list[str] = []
        for src in pair.home.script_srcs:
            s = src.lower()
            if "arkoselabs.com" in s or "funcaptcha.com" in s:
                markers.append(f"script src: {src}")
                break
        body = pair.home.body_lower
        if not markers and ("arkoselabs" in body or "funcaptcha" in body):
            markers.append("arkose/funcaptcha body reference")
        if not markers:
            return BaseMatch()
        confidence_loaded = any("script" in m for m in markers)
        extra = {"loaded": "true" if confidence_loaded else "false"}
        return BaseMatch(markers=markers, extra=extra)


arkose = Arkose._runner  # type: ignore[attr-defined]
