"""Next.js — base + Pages Router / App Router / header-only variants
plus version capture from x-powered-by."""
from __future__ import annotations

from site_profiler.detectors.framework.nextjs import nextjs
from tests.conftest import make_pair


def _detect(**kw):
    return nextjs(make_pair(home_kwargs=kw))


def test_pages_router_via_next_data():
    html = '<html><body><script id="__NEXT_DATA__" type="application/json">{"buildId":"abc"}</script></body></html>'
    ev = _detect(html=html)
    assert ev is not None
    assert "pages_router" in ev.extra.get("mode", "")
    names = {v.name for v in ev.variants}
    assert "pages_router" in names


def test_app_router_via_streaming_rsc():
    html = (
        '<html><body><script>self.__next_f.push([1,"x"]);self.__next_f.push([2,"y"]);</script></body></html>'
    )
    ev = _detect(
        html=html,
        headers={"vary": "rsc, next-router-state-tree"},
    )
    assert ev is not None
    names = {v.name for v in ev.variants}
    assert "app_router" in names
    assert "pages_router" not in names


def test_header_only_variant_when_no_body_signals():
    ev = _detect(headers={
        "x-powered-by": "Next.js",
        "x-nextjs-prerender": "1",
    })
    assert ev is not None
    names = {v.name for v in ev.variants}
    assert "header_only" in names
    assert "pages_router" not in names


def test_header_only_suppressed_when_pages_router_matches():
    html = '<html><body><script id="__NEXT_DATA__">{}</script></body></html>'
    ev = _detect(html=html, headers={"x-powered-by": "Next.js"})
    names = {v.name for v in ev.variants}
    assert "pages_router" in names
    assert "header_only" not in names


def test_version_capture_from_x_powered_by():
    ev = _detect(headers={"x-powered-by": "Next.js 13.4.0"})
    assert ev is not None
    assert ev.version == "13.4.0"


def test_no_signals_no_evidence():
    ev = _detect(html="<html><body>nothing</body></html>")
    assert ev is None
