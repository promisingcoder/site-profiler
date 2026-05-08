"""Shopify — base + core / hydrogen / oxygen variants."""
from __future__ import annotations

from site_profiler.detectors.framework.shopify import shopify, shopify_hydrogen
from tests.conftest import make_pair


def _detect(**kw):
    return shopify(make_pair(home_kwargs=kw))


def test_core_variant():
    ev = _detect(
        html='<script>window.Shopify={theme:{}};</script><script src="https://cdn.shopify.com/x.js"></script>',
        headers={"powered-by": "Shopify"},
        set_cookies=["_shopify_y=a", "_shopify_essential=b"],
    )
    assert ev is not None
    names = {v.name for v in ev.variants}
    assert "core" in names


def test_hydrogen_variant():
    ev = _detect(
        headers={
            "powered-by": "Shopify, Hydrogen",
        },
    )
    assert ev is not None
    names = {v.name for v in ev.variants}
    assert "hydrogen" in names


def test_oxygen_variant():
    ev = _detect(
        headers={
            "powered-by": "Shopify, Oxygen, Hydrogen",
            "oxygen-full-page-cache": "uncacheable",
        },
    )
    assert ev is not None
    names = {v.name for v in ev.variants}
    assert "oxygen" in names
    assert "hydrogen" in names  # both fire on Oxygen-hosted Hydrogen


def test_legacy_shopify_hydrogen_evidence_still_fires():
    """The standalone shopify_hydrogen Evidence is preserved for the
    strategy ranker; tests for it must keep working."""
    pair = make_pair(home_kwargs={"headers": {"powered-by": "Shopify, Hydrogen"}})
    ev = shopify_hydrogen(pair)
    assert ev is not None
    assert ev.name == "shopify_hydrogen"


def test_no_shopify_no_evidence():
    ev = _detect(html="<html><body>none</body></html>")
    assert ev is None
