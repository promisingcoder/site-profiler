"""Tests for the detector base machinery itself.

These tests don't talk to any specific framework / captcha — they verify:
    - the @register-on-subclass mechanism (Detector / PatternDetector),
    - the abstract gate (intermediate ABCs don't auto-register),
    - the variant probe wiring (probes get instantiated, exceptions caught),
    - Pattern matchers each return the expected (markers, version) shape.
"""
from __future__ import annotations

import re

import pytest

from site_profiler.detectors.base import (
    BaseMatch,
    BodyRegexPattern,
    BodySubstrPattern,
    CookiePattern,
    CSPHostPattern,
    Detector,
    HeaderPattern,
    HeaderPrefixPattern,
    HtmlAttrPattern,
    MetaGeneratorPattern,
    PatternDetector,
    ScriptHostPattern,
    ScriptSrcPattern,
    VariantProbe,
)
from site_profiler.registry import _REGISTRY, get_detectors
from site_profiler.schema import Variant
from tests.conftest import make_pair


# --- registration mechanics ------------------------------------------------


def test_intermediate_abstract_classes_do_not_register():
    """``Detector`` and ``PatternDetector`` themselves must not be in the
    registry — they're ABCs."""
    fn_names_all: set[str] = set()
    for cat in _REGISTRY:
        fn_names_all.update(fn.__name__ for fn in _REGISTRY[cat])
    assert "Detector" not in fn_names_all
    assert "PatternDetector" not in fn_names_all


def test_concrete_subclass_auto_registers_and_runs():
    # define a fresh detector entirely inside the test, then unregister
    class _Probe(VariantProbe):
        name = "probe_one"
        label = "probe one"

        def probe(self, pair):
            return Variant(name=self.name, label=self.label, confidence=0.5, markers=["fixed"])

    class _Test(Detector):
        name = "_test_detector_xyz"
        category = "_test"
        base_confidence = 0.7
        variants = (_Probe,)
        abstract = False

        def base_match(self, pair):
            return BaseMatch(markers=["base"], extra={"k": "v"})

    try:
        fns = get_detectors("_test")
        assert any(f.__name__ == "_test_detector_xyz" for f in fns)
        ev = _Test._instance.detect(make_pair())
        assert ev is not None
        assert ev.markers == ["base"]
        assert ev.extra == {"k": "v"}
        assert len(ev.variants) == 1
        assert ev.variants[0].name == "probe_one"
    finally:
        # tear down
        _REGISTRY["_test"] = [
            f for f in _REGISTRY.get("_test", []) if f.__name__ != "_test_detector_xyz"
        ]


def test_detector_without_name_or_category_raises():
    with pytest.raises(TypeError):
        class _Bad(Detector):
            abstract = False

            def base_match(self, pair):
                return BaseMatch()


def test_variant_probe_exception_is_caught_not_propagated():
    class _BoomProbe(VariantProbe):
        name = "boom"
        label = "boom"

        def probe(self, pair):
            raise RuntimeError("boom")

    class _T2(Detector):
        name = "_test_boom_detector"
        category = "_test_boom"
        variants = (_BoomProbe,)
        abstract = False

        def base_match(self, pair):
            return BaseMatch(markers=["base"])

    try:
        ev = _T2._instance.detect(make_pair())
        assert ev is not None
        # Variant exception is captured as a synthetic _probe_error variant
        names = {v.name for v in ev.variants}
        assert any(n.startswith("_probe_error") for n in names)
    finally:
        _REGISTRY["_test_boom"] = [
            f for f in _REGISTRY.get("_test_boom", []) if f.__name__ != "_test_boom_detector"
        ]


def test_marker_count_bumps_confidence_with_ceiling():
    class _Many(Detector):
        name = "_many_markers"
        category = "_test_many"
        base_confidence = 0.85
        abstract = False

        def base_match(self, pair):
            return BaseMatch(markers=["a", "b", "c", "d", "e", "f", "g"])

    try:
        ev = _Many._instance.detect(make_pair())
        # 7 markers → 6 bonus * 0.05 = 0.30 → 0.85 + 0.30 = 1.15 → capped at 0.99
        assert ev.confidence <= 0.99
        assert ev.confidence >= 0.95
    finally:
        _REGISTRY["_test_many"] = []


# --- HeaderPattern ---------------------------------------------------------


def test_header_pattern_presence():
    p = HeaderPattern("server")
    pair = make_pair(home_kwargs={"headers": {"server": "nginx"}})
    markers, ver = p.scan(pair)
    assert markers == ["server header"]
    assert ver is None


def test_header_pattern_regex_with_version():
    p = HeaderPattern(
        "x-aspnet-version",
        re.compile(r"^([\d.]+)$"),
        capture_version=True,
    )
    pair = make_pair(home_kwargs={"headers": {"x-aspnet-version": "4.0.30319"}})
    markers, ver = p.scan(pair)
    assert ver == "4.0.30319"
    assert markers


def test_header_pattern_no_match_returns_empty():
    p = HeaderPattern("server", re.compile(r"^Apache"))
    pair = make_pair(home_kwargs={"headers": {"server": "nginx"}})
    markers, ver = p.scan(pair)
    assert markers == []
    assert ver is None


# --- HeaderPrefixPattern ---------------------------------------------------


def test_header_prefix_pattern_finds_all():
    p = HeaderPrefixPattern("x-bubble-")
    pair = make_pair(home_kwargs={"headers": {
        "x-bubble-perf": "1",
        "x-bubble-capacity-used": "2",
        "x-other": "3",
    }})
    markers, _ = p.scan(pair)
    assert len(markers) == 2


# --- ScriptSrcPattern ------------------------------------------------------


def test_script_src_pattern_substring():
    p = ScriptSrcPattern("/_astro/")
    pair = make_pair(home_kwargs={"html": '<script src="/_astro/page.abc.js"></script>'})
    markers, _ = p.scan(pair)
    assert markers == ["script src: /_astro/page.abc.js"]


def test_script_src_pattern_regex_with_version():
    p = ScriptSrcPattern(
        substr="",
        pattern=re.compile(r"vue[.-](\d+\.\d+\.\d+)\.min\.js"),
    )
    pair = make_pair(home_kwargs={"html": '<script src="/vendor/vue-3.4.21.min.js"></script>'})
    markers, ver = p.scan(pair)
    assert ver == "3.4.21"
    assert markers


# --- ScriptHostPattern -----------------------------------------------------


def test_script_host_pattern():
    p = ScriptHostPattern("cdn.shopify.com")
    pair = make_pair(home_kwargs={"html": '<script src="https://cdn.shopify.com/x.js"></script>'})
    markers, _ = p.scan(pair)
    assert any("cdn.shopify.com" in m for m in markers)


# --- CookiePattern ---------------------------------------------------------


def test_cookie_pattern_substring():
    p = CookiePattern(substr="laravel_session")
    pair = make_pair(home_kwargs={"set_cookies": ["laravel_session=abc"]})
    markers, _ = p.scan(pair)
    assert markers == ["cookie: laravel_session"]


def test_cookie_pattern_regex():
    p = CookiePattern(pattern=re.compile(r"^_shopify_"))
    pair = make_pair(home_kwargs={"set_cookies": ["_shopify_y=a", "other=b"]})
    markers, _ = p.scan(pair)
    assert markers == ["cookie: _shopify_y"]


# --- BodySubstrPattern -----------------------------------------------------


def test_body_substr_pattern_min_count():
    p = BodySubstrPattern("wp-content/", min_count=3)
    html = "x" + ("wp-content/y" * 5) + "x"
    pair = make_pair(home_kwargs={"html": f"<html><body>{html}</body></html>"})
    markers, _ = p.scan(pair)
    assert markers and "x5" in markers[0]


def test_body_substr_pattern_below_min_count():
    p = BodySubstrPattern("wp-content/", min_count=5)
    html = "wp-content/" * 3
    pair = make_pair(home_kwargs={"html": f"<html><body>{html}</body></html>"})
    markers, _ = p.scan(pair)
    assert markers == []


# --- BodyRegexPattern ------------------------------------------------------


def test_body_regex_pattern_with_version_capture():
    p = BodyRegexPattern(
        re.compile(r"q:version=\"([\d.]+)\"", re.I),
        label="q:version",
        capture_version=True,
    )
    pair = make_pair(home_kwargs={"html": '<html q:version="1.5.2"></html>'})
    markers, ver = p.scan(pair)
    assert markers == ["q:version"]
    assert ver == "1.5.2"


# --- MetaGeneratorPattern --------------------------------------------------


def test_meta_generator_with_version_capture():
    p = MetaGeneratorPattern(
        re.compile(r"^WordPress(?:\s+([\d.]+))?", re.I),
        capture_version=True,
    )
    pair = make_pair(home_kwargs={"html": '<head><meta name="generator" content="WordPress 6.4.2"></head>'})
    markers, ver = p.scan(pair)
    assert markers
    assert ver == "6.4.2"


# --- HtmlAttrPattern -------------------------------------------------------


def test_html_attr_pattern_on_html_root():
    p = HtmlAttrPattern("data-sveltekit-")
    pair = make_pair(home_kwargs={"html": '<html data-sveltekit-preload-data="hover"><body></body></html>'})
    markers, _ = p.scan(pair)
    assert markers


# --- CSPHostPattern --------------------------------------------------------


def test_csp_host_pattern():
    p = CSPHostPattern("recaptcha")
    pair = make_pair(home_kwargs={"headers": {
        "content-security-policy": "script-src 'self' https://www.recaptcha.net",
    }})
    markers, _ = p.scan(pair)
    assert any("recaptcha" in m for m in markers)


# --- PatternDetector end-to-end -------------------------------------------


def test_pattern_detector_aggregates_markers_and_version():
    class _PD(PatternDetector):
        name = "_pd_test"
        category = "_test_pd"
        abstract = False
        matchers = (
            HeaderPattern("server"),
            BodySubstrPattern("foobar"),
            BodyRegexPattern(
                re.compile(r"version\s*=\s*\"([\d.]+)\""),
                label="version attr",
                capture_version=True,
            ),
        )

    try:
        pair = make_pair(home_kwargs={
            "headers": {"server": "nginx"},
            "html": '<html><body>foobar</body><div version="1.2.3"></div></html>',
        })
        ev = _PD._instance.detect(pair)
        assert ev is not None
        assert "server header" in ev.markers
        assert ev.version == "1.2.3"
    finally:
        from site_profiler.registry import _REGISTRY
        _REGISTRY["_test_pd"] = []
