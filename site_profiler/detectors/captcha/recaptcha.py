"""Google reCAPTCHA detector.

Variants distinguished:
    - ``v2_checkbox``: visible "I'm not a robot" widget (most common loader form).
    - ``v2_invisible``: badge-only widget invoked from a button.
    - ``v3``: scoring-only, no widget (``api.js?render=<site_key>``).
    - ``enterprise``: ``enterprise.js`` script + ``grecaptcha.enterprise.*`` API.

A page can match more than one variant (a site can render v2 widgets and
also call ``grecaptcha.execute`` for an invisible challenge), in which case
all matched variants are reported.

References used during detection design:
    - https://developers.google.com/recaptcha/docs/versions
    - https://docs.cloud.google.com/recaptcha/docs/api-ref-checkbox-keys
"""
from __future__ import annotations

from ...parse import FetchedPair
from ...schema import Variant
from ..base import (
    BaseMatch,
    Detector,
    VariantProbe,
)


def _has_recaptcha_script(pair: FetchedPair) -> tuple[list[str], bool, bool]:
    """Returns (markers, has_enterprise_path, has_v3_render_param)."""
    markers: list[str] = []
    enterprise = False
    has_render_param = False
    for src in pair.home.script_srcs:
        s = src.lower()
        if "/recaptcha/" in s or "recaptcha.net" in s or "google.com/recaptcha" in s:
            markers.append(f"script src: {src}")
            if "enterprise.js" in s:
                enterprise = True
            if "render=" in s:
                # ?render=<sitekey> is a v3 marker; ?render=explicit is v2 explicit
                if "render=explicit" not in s:
                    has_render_param = True
    return markers, enterprise, has_render_param


class RecaptchaV2Checkbox(VariantProbe):
    name = "v2_checkbox"
    label = "reCAPTCHA v2 (checkbox)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        body = pair.home.body_lower
        if 'class="g-recaptcha"' in body or "class='g-recaptcha'" in body:
            markers.append("g-recaptcha widget element")
        if 'data-sitekey=' in body and "g-recaptcha" in body:
            markers.append("g-recaptcha + data-sitekey")
        # iframe form (after solve)
        if "recaptcha/api2/anchor" in body:
            markers.append("recaptcha/api2/anchor iframe")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.95, markers=markers)


class RecaptchaV2Invisible(VariantProbe):
    name = "v2_invisible"
    label = "reCAPTCHA v2 (invisible)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        body = pair.home.body_lower
        markers: list[str] = []
        if 'data-size="invisible"' in body and "g-recaptcha" in body:
            markers.append('data-size="invisible" on g-recaptcha element')
        if "recaptcha/api2/bframe" in body:
            markers.append("recaptcha/api2/bframe iframe")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.9, markers=markers)


class RecaptchaV3(VariantProbe):
    name = "v3"
    label = "reCAPTCHA v3"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        for src in pair.home.script_srcs:
            s = src.lower()
            # Distinct v3 markers: api.js?render=<sitekey> (not "render=explicit")
            if "/recaptcha/api.js" in s and "render=" in s and "render=explicit" not in s:
                markers.append(f"v3 loader: {src}")
        body = pair.home.body_lower
        if "grecaptcha.execute(" in body and "grecaptcha.enterprise" not in body:
            markers.append("grecaptcha.execute(...) call (v3 scoring API)")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.9, markers=markers)


class RecaptchaEnterprise(VariantProbe):
    name = "enterprise"
    label = "reCAPTCHA Enterprise"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        for src in pair.home.script_srcs:
            if "enterprise.js" in src.lower() and "recaptcha" in src.lower():
                markers.append(f"enterprise.js: {src}")
        body = pair.home.body_lower
        if "grecaptcha.enterprise" in body:
            markers.append("grecaptcha.enterprise.* API call")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.95, markers=markers)


class Recaptcha(Detector):
    name = "recaptcha"
    category = "captcha"
    base_confidence = 0.95
    variants = (RecaptchaV2Checkbox, RecaptchaV2Invisible, RecaptchaV3, RecaptchaEnterprise)
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        markers, _enterprise, _v3 = _has_recaptcha_script(pair)
        # CSP-only allowlisting: weaker — just informational, captured separately
        # by csp_hints. Still we mention it as a marker.
        if not markers:
            for d, srcs in pair.home.csp.items():
                for src in srcs:
                    if "recaptcha" in src.lower():
                        markers.append(f"csp {d}: {src} (allowlisted only)")
                        break
                if markers:
                    break
        if not markers:
            return BaseMatch()
        extra = {"loaded": "true"} if any("script src" in m for m in markers) else {"loaded": "false"}
        return BaseMatch(markers=markers, extra=extra)


# Module-level alias — matches the name detectors are registered under so
# direct imports (``from .recaptcha import recaptcha``) keep working.
recaptcha = Recaptcha._runner  # type: ignore[attr-defined]
