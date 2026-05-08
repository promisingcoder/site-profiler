"""Tests for the Wappalyzer-grounded framework detectors added in this
release. One test per detector with a positive case + negative confirmation.

Per-detector signal density is intentionally low here — these are smoke
tests that prove the matcher pipeline registers, runs, and detects on the
canonical marker. Deeper variant tests (Magento 1 vs 2, ASP.NET Classic
vs Core) live in their own dedicated files.
"""
from __future__ import annotations

import re

from site_profiler.registry import get_detectors
from tests.conftest import make_pair


def _registry_lookup(name: str):
    """Return the registered runner with the given name (raises if missing)."""
    for fn in get_detectors("framework"):
        if fn.__name__ == name:
            return fn
    raise AssertionError(f"detector {name!r} not registered as framework")


def _run(name: str, **kw):
    return _registry_lookup(name)(make_pair(home_kwargs=kw))


# --- Astro -----------------------------------------------------------------


def test_astro_via_generator_with_version():
    ev = _run("astro", html='<html><head><meta name="generator" content="Astro v4.5.1"></head></html>')
    assert ev is not None
    assert ev.version == "4.5.1"


def test_astro_via_island():
    ev = _run("astro", html='<html><body><astro-island></astro-island></body></html>')
    assert ev is not None


def test_astro_negative():
    ev = _run("astro", html="<html><body>nothing</body></html>")
    assert ev is None


# --- SvelteKit -------------------------------------------------------------


def test_sveltekit_via_announcer():
    ev = _run("sveltekit", html='<div id="svelte-announcer">x</div>')
    assert ev is not None


def test_sveltekit_negative():
    ev = _run("sveltekit", html="<html><body>x</body></html>")
    assert ev is None


# --- Svelte ----------------------------------------------------------------


def test_svelte_via_data_svelte_h_hash():
    ev = _run("svelte", html='<div data-svelte-h="svelte-abcdef1">x</div>')
    assert ev is not None


def test_svelte_negative():
    ev = _run("svelte", html="<html><body>none</body></html>")
    assert ev is None


# --- Remix -----------------------------------------------------------------


def test_remix_via_global():
    ev = _run("remix", html='<script>window.__remixContext={};</script>')
    assert ev is not None


def test_remix_negative():
    ev = _run("remix", html="<html><body>none</body></html>")
    assert ev is None


# --- SolidStart ------------------------------------------------------------


def test_solid_start_via_hy_init():
    ev = _run("solid_start", html='<script>_$HY.init();</script>')
    assert ev is not None


# --- Qwik ------------------------------------------------------------------


def test_qwik_via_q_version_attribute():
    ev = _run("qwik", html='<html q:version="1.5.2"><body><div q:container q:base="/build/"></div></body></html>')
    assert ev is not None
    assert ev.version == "1.5.2"


# --- Angular (modern) ------------------------------------------------------


def test_angular_via_ng_version():
    ev = _run("angular", html='<html><body><app-root ng-version="17.3.4"></app-root></body></html>')
    assert ev is not None
    assert ev.version == "17.3.4"


def test_angular_negative_does_not_match_angularjs():
    """ng-app= is AngularJS, not modern Angular; must not fire on this."""
    ev = _run("angular", html='<html ng-app="myApp"><body></body></html>')
    assert ev is None


# --- AngularJS -------------------------------------------------------------


def test_angularjs_via_ng_app():
    ev = _run("angularjs", html='<html ng-app="myApp"><body><div ng-controller="X"></div></body></html>')
    assert ev is not None


def test_angularjs_via_loader_with_version():
    ev = _run(
        "angularjs",
        html='<html><body><script src="/lib/angular-1.7.9.min.js"></script><div ng-app="x"></div></body></html>',
    )
    assert ev is not None
    assert ev.version == "1.7.9"


# --- Vue (vanilla) ---------------------------------------------------------


def test_vue_via_data_v_attribute():
    ev = _run("vue", html='<html><body><div data-v-app><span data-v-abcdef>x</span></div></body></html>')
    assert ev is not None


def test_vue_via_loader_with_version():
    ev = _run("vue", html='<script src="/vendor/vue-3.4.21.min.js"></script>')
    assert ev is not None
    assert ev.version == "3.4.21"


# --- React (vanilla) -------------------------------------------------------


def test_react_via_loader_with_version():
    ev = _run("react", html='<script src="/dist/react-18.2.0.min.js"></script>')
    assert ev is not None
    assert ev.version == "18.2.0"


def test_react_via_root_container():
    ev = _run("react", html='<html><body><div id="root" data-reactroot="" _reactrootcontainer></div></body></html>')
    assert ev is not None


# --- Magento (1 vs 2 variants) ---------------------------------------------


def test_magento_v1_variant():
    ev = _run(
        "magento",
        html='<html><body><script src="/js/mage/cookies.js"></script>'
             '<link href="/skin/frontend/enterprise/x/style.css"></body></html>',
    )
    assert ev is not None
    names = {v.name for v in ev.variants}
    assert "v1" in names


def test_magento_v2_variant():
    ev = _run(
        "magento",
        html='<html><body><script type="text/x-magento-init">{}</script>'
             '<script src="/static/_requirejs/x.js"></script></body></html>',
    )
    assert ev is not None
    names = {v.name for v in ev.variants}
    assert "v2" in names


# --- Joomla ----------------------------------------------------------------


def test_joomla_via_generator_with_version():
    ev = _run("joomla", html='<html><head><meta name="generator" content="Joomla! 4.4.0"></head></html>')
    assert ev is not None
    assert ev.version == "4.4.0"


# --- Squarespace -----------------------------------------------------------


def test_squarespace_via_server_header():
    ev = _run("squarespace", headers={"server": "Squarespace"})
    assert ev is not None


# --- Laravel ---------------------------------------------------------------


def test_laravel_via_session_cookie():
    ev = _run("laravel", set_cookies=["laravel_session=abc"])
    assert ev is not None


# --- Django ----------------------------------------------------------------


def test_django_via_csrf_input():
    ev = _run(
        "django",
        html='<form><input type="hidden" name="csrfmiddlewaretoken" value="x"></form>',
    )
    assert ev is not None


# --- Rails -----------------------------------------------------------------


def test_rails_via_csrf_param_meta():
    ev = _run(
        "rails",
        html='<head><meta name="csrf-param" content="authenticity_token"></head>',
    )
    assert ev is not None


# --- ASP.NET (variants) ----------------------------------------------------


def test_aspnet_classic_variant_via_viewstate():
    ev = _run(
        "asp.net",
        html='<form><input type="hidden" name="__VIEWSTATE" value="abc"/></form>',
        headers={"x-aspnet-version": "4.0.30319"},
    )
    assert ev is not None
    assert ev.version == "4.0.30319"
    names = {v.name for v in ev.variants}
    assert "aspnet_classic" in names


def test_aspnet_core_variant_via_cookie():
    ev = _run("asp.net", set_cookies=[".AspNetCore.Antiforgery=abc"])
    assert ev is not None
    names = {v.name for v in ev.variants}
    assert "aspnet_core" in names


# --- Express ---------------------------------------------------------------


def test_express_via_powered_by():
    ev = _run("express", headers={"x-powered-by": "Express"})
    assert ev is not None


# --- Strapi ----------------------------------------------------------------


def test_strapi_via_powered_by():
    ev = _run("strapi", headers={"x-powered-by": "Strapi <strapi.io>"})
    assert ev is not None


# --- Sanity ----------------------------------------------------------------


def test_sanity_via_cdn_host():
    ev = _run(
        "sanity",
        html='<img src="https://cdn.sanity.io/images/abc/production/x.jpg">',
    )
    assert ev is not None


# --- Contentful ------------------------------------------------------------


def test_contentful_via_asset_url():
    ev = _run(
        "contentful",
        html='<img src="https://images.ctfassets.net/abc/x.jpg">',
    )
    assert ev is not None


# --- Bubble ----------------------------------------------------------------


def test_bubble_via_x_bubble_header():
    ev = _run("bubble", headers={"x-bubble-perf": '{"a":1}'})
    assert ev is not None


# --- Framer ----------------------------------------------------------------


def test_framer_via_usercontent_host():
    ev = _run(
        "framer",
        html='<img src="https://framerusercontent.com/images/x.png">',
    )
    assert ev is not None


# --- Storyblok -------------------------------------------------------------


def test_storyblok_via_asset_host():
    ev = _run(
        "storyblok",
        html='<img src="https://a.storyblok.com/f/abc/x/y.png">',
    )
    assert ev is not None
