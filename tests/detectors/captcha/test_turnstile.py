"""Cloudflare Turnstile — base + managed / non-interactive / invisible."""
from __future__ import annotations

from site_profiler.detectors.captcha.turnstile import turnstile
from tests.conftest import make_pair


def _detect(html: str = "", **kw):
    return turnstile(make_pair(home_kwargs={"html": html, **kw}))


def test_base_loader():
    ev = _detect(
        '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>'
    )
    assert ev is not None
    assert ev.name == "turnstile"


def test_managed_default_variant():
    ev = _detect(
        '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>'
        '<div class="cf-turnstile" data-sitekey="abc"></div>'
    )
    names = {v.name for v in ev.variants}
    assert "managed" in names


def test_non_interactive_variant():
    ev = _detect(
        '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>'
        '<div class="cf-turnstile" data-sitekey="abc" data-appearance="non-interactive"></div>'
    )
    names = {v.name for v in ev.variants}
    assert "non_interactive" in names
    assert "managed" not in names


def test_invisible_variant():
    ev = _detect(
        '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>'
        '<div class="cf-turnstile" data-sitekey="abc" data-size="invisible"></div>'
        '<script>turnstile.execute("#widget");</script>'
    )
    names = {v.name for v in ev.variants}
    assert "invisible" in names


def test_no_turnstile_no_evidence():
    ev = _detect("<html><body>nothing</body></html>")
    assert ev is None
