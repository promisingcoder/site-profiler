"""DataDome captcha challenge surface."""
from __future__ import annotations

from site_profiler.detectors.captcha.datadome_captcha import datadome_captcha
from tests.conftest import make_pair


def _detect(html: str = "", **kw):
    return datadome_captcha(make_pair(home_kwargs={"html": html, **kw}))


def test_via_container_div_and_global():
    ev = _detect(
        '<div id="datadome-container"></div>'
        '<script>var datadomeClientKey = "abc";</script>'
    )
    assert ev is not None
    assert ev.name == "datadome_captcha"


def test_via_captcha_delivery_iframe():
    ev = _detect(
        '<iframe src="https://geo.captcha-delivery.com/captcha/?initialCid=abc"></iframe>'
    )
    assert ev is not None


def test_block_title_with_datadome_reference():
    html = (
        "<html><head><title>blocked</title></head>"
        "<body>powered by datadome</body></html>"
    )
    ev = _detect(html=html)
    assert ev is not None


def test_no_datadome_no_evidence():
    ev = _detect(html="<html><body>plain</body></html>")
    assert ev is None
