from site_profiler.detectors.bot_protection.cloudflare_bm import cloudflare_bm
from site_profiler.detectors.bot_protection.datadome import datadome
from site_profiler.detectors.bot_protection.perimeterx import perimeterx
from site_profiler.detectors.captcha.aws_waf_captcha import aws_waf_captcha
from site_profiler.detectors.captcha.recaptcha import recaptcha
from site_profiler.detectors.captcha.turnstile import turnstile
from site_profiler.detectors.edge.akamai import akamai
from site_profiler.detectors.edge.cloudflare import cloudflare
from site_profiler.detectors.edge.cloudfront import cloudfront
from site_profiler.detectors.edge.fastly import fastly
from site_profiler.detectors.edge.vercel import vercel
from site_profiler.detectors.framework.drupal import drupal
from site_profiler.detectors.framework.hubspot import hubspot
from site_profiler.detectors.framework.nextjs import nextjs
from site_profiler.detectors.framework.shopify import shopify, shopify_hydrogen
from site_profiler.detectors.framework.sphinx import sphinx
from site_profiler.detectors.framework.webflow import webflow
from site_profiler.detectors.framework.wordpress import wordpress

from .conftest import make_pair


def test_cloudflare_two_signals():
    pair = make_pair(home_kwargs={
        "headers": {"server": "cloudflare", "cf-ray": "abc-MRS"},
    })
    ev = cloudflare(pair)
    assert ev is not None
    assert ev.confidence >= 0.99


def test_cloudflare_envoy_two_word_server():
    pair = make_pair(home_kwargs={
        "headers": {"server": "cloudflare envoy", "cf-ray": "abc-PMO"},
    })
    ev = cloudflare(pair)
    assert ev is not None


def test_cloudfront_multi_marker():
    pair = make_pair(home_kwargs={
        "headers": {
            "server": "CloudFront",
            "via": "1.1 abc.cloudfront.net (CloudFront)",
            "x-amz-cf-id": "abc",
            "x-amz-cf-pop": "MRS53-P2",
        },
    })
    ev = cloudfront(pair)
    assert ev is not None
    assert ev.confidence >= 0.99


def test_fastly_pop_pattern():
    pair = make_pair(home_kwargs={
        "headers": {"via": "1.1 varnish", "x-served-by": "cache-lin1730055-LIN"},
    })
    ev = fastly(pair)
    assert ev is not None


def test_fastly_lone_varnish_does_not_match():
    pair = make_pair(home_kwargs={"headers": {"via": "1.1 varnish"}})
    ev = fastly(pair)
    assert ev is None  # Varnish alone is not enough


def test_akamai_via_ghost():
    pair = make_pair(home_kwargs={
        "headers": {"server": "AkamaiGHost", "x-akamai-transformed": "9 42113 0"},
    })
    ev = akamai(pair)
    assert ev is not None


def test_akamai_via_cookies_only():
    pair = make_pair(home_kwargs={"set_cookies": ["AKA_A2=x", "akavpau_p2=y"]})
    ev = akamai(pair)
    assert ev is not None


def test_vercel():
    pair = make_pair(home_kwargs={
        "headers": {"x-vercel-id": "fra1::abc", "x-vercel-cache": "HIT"},
    })
    ev = vercel(pair)
    assert ev is not None


def test_shopify_full_signal():
    html = '<html><body><script>window.Shopify = {theme:{}};</script><script src="https://cdn.shopify.com/s/x.js"></script></body></html>'
    pair = make_pair(home_kwargs={
        "html": html,
        "headers": {"powered-by": "Shopify", "shopify-complexity-score": "0"},
        "set_cookies": ["_shopify_y=a", "_shopify_essential=b"],
    })
    ev = shopify(pair)
    assert ev is not None
    assert ev.confidence >= 0.99


def test_shopify_hydrogen():
    pair = make_pair(home_kwargs={
        "headers": {
            "powered-by": "Shopify, Oxygen, Hydrogen",
            "oxygen-full-page-cache": "uncacheable",
        },
    })
    ev = shopify_hydrogen(pair)
    assert ev is not None


def test_wordpress_link_header():
    pair = make_pair(home_kwargs={
        "headers": {"link": '<https://example.com/wp-json/>; rel="https://api.w.org/"'},
        "html": "<html><body>" + ('<a href="/wp-content/x">x</a>' * 10) + "</body></html>",
    })
    ev = wordpress(pair)
    assert ev is not None


def test_wordpress_via_cf_edge_cache():
    pair = make_pair(home_kwargs={
        "headers": {"cf-edge-cache": "cache,platform=wordpress"},
        "html": "<html><body>" + ('<a href="/wp-content/x">x</a>' * 10) + "</body></html>",
    })
    ev = wordpress(pair)
    assert ev is not None


def test_drupal_via_x_generator():
    pair = make_pair(home_kwargs={"headers": {"x-generator": "Drupal 10 (https://www.drupal.org)"}})
    ev = drupal(pair)
    assert ev is not None


def test_webflow_x_wf_headers():
    pair = make_pair(home_kwargs={
        "headers": {"x-wf-region": "us-east-1", "x-wf-page-id": "abc"},
        "html": '<html><body><script src="https://cdn.prod.website-files.com/x.js"></script></body></html>',
    })
    ev = webflow(pair)
    assert ev is not None


def test_hubspot_x_hs_headers():
    pair = make_pair(home_kwargs={
        "headers": {"x-hs-content-id": "1", "x-hs-hub-id": "2"},
    })
    ev = hubspot(pair)
    assert ev is not None


def test_sphinx_via_generator():
    html = '<html><head><meta name="generator" content="Sphinx 5.0"></head><body><div class="sphinxsidebar">x</div></body></html>'
    pair = make_pair(home_kwargs={"html": html})
    ev = sphinx(pair)
    assert ev is not None


def test_nextjs_pages_router_via_next_data():
    html = '<html><body><script id="__NEXT_DATA__" type="application/json">{"buildId":"abc","props":{}}</script></body></html>'
    pair = make_pair(home_kwargs={"html": html})
    ev = nextjs(pair)
    assert ev is not None
    assert "pages_router" in ev.extra.get("mode", "")


def test_nextjs_app_router_via_vary():
    html = '<html><body><script>self.__next_f.push([1,"data"]);self.__next_f.push([2,"more"]);</script></body></html>'
    pair = make_pair(home_kwargs={
        "html": html,
        "headers": {"vary": "rsc, next-router-state-tree, next-router-prefetch"},
    })
    ev = nextjs(pair)
    assert ev is not None
    assert "app_router" in ev.extra.get("mode", "")


def test_nextjs_header_only():
    pair = make_pair(home_kwargs={
        "headers": {
            "x-powered-by": "Next.js, Payload",
            "x-nextjs-prerender": "1",
            "x-nextjs-stale-time": "300",
        },
    })
    ev = nextjs(pair)
    assert ev is not None


def test_recaptcha_loaded():
    pair = make_pair(home_kwargs={
        "html": '<html><body><script src="https://www.google.com/recaptcha/api.js?render=site_key"></script></body></html>',
    })
    ev = recaptcha(pair)
    assert ev is not None
    assert ev.extra.get("loaded") == "true"


def test_turnstile_loaded():
    pair = make_pair(home_kwargs={
        "html": '<html><body><script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script></body></html>',
    })
    ev = turnstile(pair)
    assert ev is not None


def test_cloudflare_bm_engaged_via_mitigated():
    pair = make_pair(home_kwargs={
        "headers": {"cf-mitigated": "challenge"},
        "set_cookies": ["__cf_bm=x"],
        "status": 403,
    })
    ev = cloudflare_bm(pair)
    assert ev is not None
    assert ev.extra.get("mode") == "engaged"


def test_cloudflare_bm_armed():
    pair = make_pair(home_kwargs={"set_cookies": ["__cf_bm=x", "_cfuvid=y"], "status": 200})
    ev = cloudflare_bm(pair)
    assert ev is not None
    assert ev.extra.get("mode") == "armed_passive"


def test_datadome_engaged():
    pair = make_pair(home_kwargs={
        "html": '<html><body><div id="datadome-container">x</div><script>var datadomeClientKey="x";</script></body></html>',
        "set_cookies": ["datadome=x"],
    })
    ev = datadome(pair)
    assert ev is not None


def test_perimeterx_via_cookies():
    pair = make_pair(home_kwargs={"set_cookies": ["_pxhd=x", "_px3=y", "_pxvid=z"]})
    ev = perimeterx(pair)
    assert ev is not None


def test_aws_waf_captcha_via_action_header():
    pair = make_pair(home_kwargs={"headers": {"x-amzn-waf-action": "captcha"}})
    ev = aws_waf_captcha(pair)
    assert ev is not None
