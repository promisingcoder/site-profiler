"""Friendly Captcha detector.

Privacy-first proof-of-work captcha (no fingerprinting, no images).
Loaded as a small widget element with class ``frc-captcha`` plus a
``data-sitekey`` attribute, with the SDK fetched from
``cdn.friendlycaptcha.com`` (or self-hosted, in which case only the
DOM marker remains).
"""
from __future__ import annotations

from ...parse import FetchedPair
from ..base import BaseMatch, Detector


class FriendlyCaptcha(Detector):
    name = "friendly_captcha"
    category = "captcha"
    base_confidence = 0.95
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        markers: list[str] = []
        for src in pair.home.script_srcs:
            if "friendlycaptcha.com" in src.lower() or "friendly-challenge" in src.lower():
                markers.append(f"script src: {src}")
        body = pair.home.body_lower
        if 'class="frc-captcha"' in body or "class='frc-captcha'" in body:
            markers.append("frc-captcha widget element")
        if not markers:
            return BaseMatch()
        return BaseMatch(markers=markers, extra={"loaded": "true"})


friendly_captcha = FriendlyCaptcha._runner  # type: ignore[attr-defined]
