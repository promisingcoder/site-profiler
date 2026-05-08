"""hCaptcha detector — base + standard / invisible / enterprise variants."""
from __future__ import annotations

from site_profiler.detectors.captcha.hcaptcha import hcaptcha
from tests.conftest import make_pair


def _detect(html: str = "", **kw):
    return hcaptcha(make_pair(home_kwargs={"html": html, **kw}))


def test_base_via_api_js():
    ev = _detect('<script src="https://js.hcaptcha.com/1/api.js"></script>')
    assert ev is not None
    assert ev.name == "hcaptcha"
    assert ev.extra.get("loaded") == "true"


def test_no_hcaptcha_no_evidence():
    ev = _detect("<html><body>nothing</body></html>")
    assert ev is None


def test_standard_variant():
    ev = _detect(
        '<script src="https://js.hcaptcha.com/1/api.js"></script>'
        '<div class="h-captcha" data-sitekey="abc"></div>'
    )
    names = {v.name for v in ev.variants}
    assert "standard" in names


def test_invisible_variant():
    ev = _detect(
        '<script src="https://js.hcaptcha.com/1/api.js"></script>'
        '<div class="h-captcha" data-sitekey="abc" data-size="invisible"></div>'
    )
    names = {v.name for v in ev.variants}
    assert "invisible" in names
    assert "standard" not in names  # data-size=invisible suppresses standard


def test_enterprise_variant():
    ev = _detect(
        '<script src="https://js.hcaptcha.com/1/api.js?endpoint=enterprise"></script>'
    )
    names = {v.name for v in ev.variants}
    assert "enterprise" in names


def test_widget_only_no_loader_still_detected():
    ev = _detect('<div class="h-captcha" data-sitekey="abc"></div>')
    assert ev is not None
    assert ev.extra.get("loaded") == "false"
