"""DataDome captcha challenge surface detector.

DataDome runs as a bot-management edge with its own captcha challenge
served from ``captcha-delivery.com`` (subdomain ``geo.captcha-delivery.com``
for the iframe host). The slider/audio inside the iframe is a customised
GeeTest implementation, but from the outer page's perspective the markers
are unmistakable: an iframe pointing at captcha-delivery.com plus a
``datadomeClientKey`` global or ``datadome-container`` element.

This detector captures the DataDome captcha *surface*. The DataDome
bot-protection vendor (cookie ``datadome``, header ``x-dd-b``) is reported
separately by ``detectors/bot_protection/datadome.py``.
"""
from __future__ import annotations

from ...parse import FetchedPair
from ..base import BaseMatch, Detector


class DataDomeCaptcha(Detector):
    name = "datadome_captcha"
    category = "captcha"
    base_confidence = 0.95
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        home = pair.home
        body_lower = home.body_lower
        markers: list[str] = []

        if "datadomeclientkey" in body_lower:
            markers.append("datadomeClientKey body marker")
        if "datadome-container" in body_lower:
            markers.append("datadome-container element")
        if "captcha-delivery.com" in body_lower:
            markers.append("captcha-delivery.com iframe/script reference")
        title_lc = home.title.strip().lower()
        if title_lc in {"bot or not?", "blocked"} and "datadome" in body_lower:
            markers.append(f"title '{home.title.strip()}' + datadome reference")

        if not markers:
            return BaseMatch()
        return BaseMatch(markers=markers, extra={"loaded": "true"})


datadome_captcha = DataDomeCaptcha._runner  # type: ignore[attr-defined]
