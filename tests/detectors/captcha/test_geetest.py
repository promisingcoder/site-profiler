"""GeeTest — base + v3 vs v4 variants."""
from __future__ import annotations

from site_profiler.detectors.captcha.geetest import geetest
from tests.conftest import make_pair


def _detect(html: str = "", **kw):
    return geetest(make_pair(home_kwargs={"html": html, **kw}))


def test_base_via_geetest_host():
    ev = _detect('<script src="https://static.geetest.com/static/js/geetest.0.0.0.js"></script>')
    assert ev is not None
    assert ev.name == "geetest"


def test_v3_variant_via_init_call():
    ev = _detect(
        '<script src="https://static.geetest.com/static/js/gt.0.4.9.js"></script>'
        '<script>initGeetest({gt: "abc", challenge: "x"}, function(){});</script>'
    )
    names = {v.name for v in ev.variants}
    assert "v3" in names
    assert "v4" not in names


def test_v4_variant_via_gcaptcha4_host():
    ev = _detect(
        '<script src="https://gcaptcha4.geetest.com/load?captcha_id=abc"></script>'
        '<script>initGeetest4({captchaId: "abc"}, function(){});</script>'
    )
    names = {v.name for v in ev.variants}
    assert "v4" in names
    assert "v3" not in names


def test_no_geetest_no_evidence():
    ev = _detect("<html><body>none</body></html>")
    assert ev is None
