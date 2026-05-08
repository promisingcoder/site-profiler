"""Arkose Labs / FunCaptcha — base + variant."""
from __future__ import annotations

from site_profiler.detectors.captcha.arkose import arkose
from tests.conftest import make_pair


def _detect(html: str = "", **kw):
    return arkose(make_pair(home_kwargs={"html": html, **kw}))


def test_base_via_arkoselabs_host():
    ev = _detect('<script src="https://client-api.arkoselabs.com/v2/abc/api.js"></script>')
    assert ev is not None
    assert ev.name == "arkose"
    names = {v.name for v in ev.variants}
    assert "funcaptcha" in names


def test_legacy_funcaptcha_host():
    ev = _detect('<script src="https://api.funcaptcha.com/fc/api/?onload=callback"></script>')
    assert ev is not None
    names = {v.name for v in ev.variants}
    assert "funcaptcha" in names


def test_no_arkose_no_evidence():
    ev = _detect("<html><body>none</body></html>")
    assert ev is None
