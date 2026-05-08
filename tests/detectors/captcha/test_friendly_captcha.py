"""Friendly Captcha (privacy-first PoW)."""
from __future__ import annotations

from site_profiler.detectors.captcha.friendly_captcha import friendly_captcha
from tests.conftest import make_pair


def _detect(html: str = "", **kw):
    return friendly_captcha(make_pair(home_kwargs={"html": html, **kw}))


def test_via_widget_class():
    ev = _detect('<div class="frc-captcha" data-sitekey="x"></div>')
    assert ev is not None
    assert ev.name == "friendly_captcha"


def test_via_cdn_loader():
    ev = _detect(
        '<script src="https://cdn.jsdelivr.net/npm/friendly-challenge/widget.min.js"></script>'
    )
    assert ev is not None


def test_no_friendly_no_evidence():
    ev = _detect("<html><body>none</body></html>")
    assert ev is None
