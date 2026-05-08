"""Cloudflare Turnstile detector.

Three widget modes per Cloudflare docs:
    - ``managed``: server decides whether to challenge (default).
    - ``non_interactive``: never prompts, runs background challenge only.
    - ``invisible``: same idea, but no widget rendered at all.

The mode is set via ``data-appearance``/``data-execution`` and the
``execute()`` API. Loader URL is the same for all modes —
``https://challenges.cloudflare.com/turnstile/v0/api.js``.
"""
from __future__ import annotations

from ...parse import FetchedPair
from ...schema import Variant
from ..base import BaseMatch, Detector, VariantProbe


def _has_turnstile_div(body_lower: str) -> bool:
    return 'class="cf-turnstile"' in body_lower or "class='cf-turnstile'" in body_lower


class TurnstileManaged(VariantProbe):
    name = "managed"
    label = "Turnstile (managed)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        body = pair.home.body_lower
        if not _has_turnstile_div(body):
            return None
        # Default mode (no data-appearance attribute) is "managed"
        if 'data-appearance="non-interactive"' in body or 'data-appearance="execute"' in body:
            return None
        return Variant(
            name=self.name, label=self.label, confidence=0.85,
            markers=["cf-turnstile widget element (default = managed)"],
        )


class TurnstileNonInteractive(VariantProbe):
    name = "non_interactive"
    label = "Turnstile (non-interactive)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        body = pair.home.body_lower
        markers: list[str] = []
        if 'data-appearance="non-interactive"' in body:
            markers.append('data-appearance="non-interactive"')
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.95, markers=markers)


class TurnstileInvisible(VariantProbe):
    name = "invisible"
    label = "Turnstile (invisible)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        body = pair.home.body_lower
        markers: list[str] = []
        # invisible flow: data-size="invisible" or data-execution="execute"
        if 'data-size="invisible"' in body and "cf-turnstile" in body:
            markers.append('data-size="invisible" on cf-turnstile')
        if 'data-execution="execute"' in body:
            markers.append('data-execution="execute" (manual invisible flow)')
        if "turnstile.execute(" in body:
            markers.append("turnstile.execute(...) JS call")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.9, markers=markers)


class Turnstile(Detector):
    name = "turnstile"
    category = "captcha"
    base_confidence = 0.95
    variants = (TurnstileManaged, TurnstileNonInteractive, TurnstileInvisible)
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        markers: list[str] = []
        for src in pair.home.script_srcs:
            s = src.lower()
            if "challenges.cloudflare.com/turnstile" in s or s.endswith("turnstile/v0/api.js"):
                markers.append(f"script src: {src}")
                break
        body = pair.home.body_lower
        if not markers and _has_turnstile_div(body):
            markers.append("cf-turnstile widget element (no loader script seen)")
        if not markers:
            return BaseMatch()
        extra = {"loaded": "true"} if any("script src" in m for m in markers) else {"loaded": "false"}
        return BaseMatch(markers=markers, extra=extra)


turnstile = Turnstile._runner  # type: ignore[attr-defined]
