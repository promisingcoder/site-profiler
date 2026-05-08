"""WordPress — markers + version capture."""
from __future__ import annotations

from site_profiler.detectors.framework.wordpress import wordpress
from tests.conftest import make_pair


def _detect(**kw):
    return wordpress(make_pair(home_kwargs=kw))


def test_link_header():
    ev = _detect(
        headers={"link": '<https://example.com/wp-json/>; rel="https://api.w.org/"'},
        html="<html><body>" + ('<a href="/wp-content/x">x</a>' * 10) + "</body></html>",
    )
    assert ev is not None


def test_version_captured_from_generator():
    ev = _detect(
        html='<html><head><meta name="generator" content="WordPress 6.4.2"></head><body>'
             + ('<a href="/wp-content/x">x</a>' * 10) + "</body></html>",
    )
    assert ev is not None
    assert ev.version == "6.4.2"


def test_no_wordpress_no_evidence():
    ev = _detect(html="<html><body>plain</body></html>")
    assert ev is None
