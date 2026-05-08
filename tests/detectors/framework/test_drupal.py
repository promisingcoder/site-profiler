"""Drupal — markers + version capture."""
from __future__ import annotations

from site_profiler.detectors.framework.drupal import drupal
from tests.conftest import make_pair


def _detect(**kw):
    return drupal(make_pair(home_kwargs=kw))


def test_via_x_generator_with_version():
    ev = _detect(headers={"x-generator": "Drupal 10 (https://www.drupal.org)"})
    assert ev is not None
    assert ev.version == "10"


def test_via_meta_generator_with_version():
    ev = _detect(html='<html><head><meta name="generator" content="Drupal 9.5.11"></head></html>')
    assert ev is not None
    assert ev.version == "9.5.11"


def test_via_drupalsettings():
    ev = _detect(html="<html><body><script>var drupalSettings = {};</script></body></html>")
    assert ev is not None


def test_no_drupal_no_evidence():
    ev = _detect(html="<html><body>plain</body></html>")
    assert ev is None
