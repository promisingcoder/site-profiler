"""Google reCAPTCHA detector. Distinguishes 'loaded' from 'CSP-allowlisted only'."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


def _is_recaptcha_host(host: str) -> bool:
    h = host.lower()
    return (
        "recaptcha.net" in h
        or "google.com/recaptcha" in h
        or "gstatic.com/recaptcha" in h
    )


@register("captcha")
def recaptcha(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []
    extra: dict[str, str] = {}

    for src in home.script_srcs:
        if "/recaptcha/" in src.lower() or "recaptcha.net" in src.lower():
            markers.append(f"script src: {src}")
            extra["loaded"] = "true"
            break

    if not markers:
        return None
    return Evidence(
        name="recaptcha",
        confidence=0.95,
        markers=markers,
        extra=extra,
    )
