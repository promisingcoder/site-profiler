"""End-to-end tests using synthetic pairs that mirror real-world recon findings."""
from site_profiler.api import profile_pair
from site_profiler.schema import BlockStatus, StrategyTier

from .conftest import make_pair


def test_allbirds_like_shopify_on_cloudflare():
    home = {
        "url": "https://www.allbirds.com/",
        "status": 200,
        "headers": {
            "server": "cloudflare",
            "cf-ray": "9f48f75c3bae2cc5-MRS",
            "cf-cache-status": "DYNAMIC",
            "powered-by": "Shopify",
            "shopify-complexity-score": "0",
        },
        "set_cookies": [
            "_shopify_y=a; Path=/",
            "_shopify_essential=b; Path=/",
            "_shopify_s=c; Path=/",
        ],
        "html": '<html><head><meta property="og:title" content="x"/></head><body><script src="https://cdn.shopify.com/s/files/x.js"></script></body></html>',
    }
    robots = {
        "url": "https://www.allbirds.com/robots.txt",
        "status": 200,
        "html": "User-agent: *\nDisallow: /admin/\nSitemap: https://www.allbirds.com/sitemap.xml\nCrawl-delay: 4\n",
    }
    pair = make_pair(home_kwargs=home, robots_kwargs=robots)
    profile = profile_pair(pair)

    edge_names = [e.name for e in profile.edge]
    assert "cloudflare" in edge_names

    fw_names = [e.name for e in profile.framework]
    assert "shopify" in fw_names

    assert profile.block_status == BlockStatus.NONE
    assert profile.strategy.tier == StrategyTier.API_DIRECT
    assert profile.robots.crawl_delay == 4.0
    assert "https://www.allbirds.com/sitemap.xml" in profile.robots.sitemap_urls


def test_indeed_like_cf_managed_challenge():
    home = {
        "url": "https://www.indeed.com/",
        "status": 403,
        "headers": {
            "server": "cloudflare",
            "cf-ray": "abc-MRS",
            "cf-mitigated": "challenge",
        },
        "set_cookies": ["__cf_bm=x"],
        "html": "<html><head><title>Security Check - Indeed.com</title></head><body>checking your browser</body></html>",
    }
    pair = make_pair(home_kwargs=home)
    profile = profile_pair(pair)
    assert profile.block_status == BlockStatus.SOFT_CHALLENGE
    assert profile.strategy.tier == StrategyTier.HEADLESS_PLUS_EVASION
    bp_names = [e.name for e in profile.bot_protection]
    assert "cloudflare_bot_management" in bp_names


def test_redfin_like_aws_waf_405():
    home = {
        "url": "https://www.redfin.com/",
        "status": 405,
        "headers": {
            "server": "CloudFront",
            "via": "1.1 abc.cloudfront.net (CloudFront)",
            "x-amzn-waf-action": "captcha",
            "x-amz-cf-id": "abc",
        },
        "html": '<html><body><script src="https://abc.captcha.awswaf.com/x.js"></script>Human Verification</body></html>',
    }
    pair = make_pair(home_kwargs=home)
    profile = profile_pair(pair)
    assert profile.block_status == BlockStatus.SOFT_CHALLENGE
    assert profile.strategy.tier == StrategyTier.HEADLESS_PLUS_EVASION
    edge_names = [e.name for e in profile.edge]
    assert "cloudfront" in edge_names


def test_tiktok_like_200_with_waf_body():
    home = {
        "url": "https://www.tiktok.com/",
        "status": 200,
        "headers": {"server": "TLB", "content-type": "text/html"},
        "html": '<html><body><p id="wci" class="_wafchallengeid">please wait...</p></body></html>',
    }
    pair = make_pair(home_kwargs=home)
    profile = profile_pair(pair)
    assert profile.block_status == BlockStatus.BODY_LIES
    assert profile.strategy.tier == StrategyTier.HEADLESS_PLUS_EVASION


def test_wapo_like_tls_block():
    home = {
        "url": "https://www.washingtonpost.com/",
        "status": None,
        "fetch_error": "ReadError: Server disconnected",
        "html": "",
    }
    robots = {
        "url": "https://www.washingtonpost.com/robots.txt",
        "status": 200,
        "html": "Sitemap: https://www.washingtonpost.com/arcio/sitemap/index/\n",
    }
    pair = make_pair(home_kwargs=home, robots_kwargs=robots)
    profile = profile_pair(pair)
    assert profile.block_status == BlockStatus.TLS_BLOCK
    assert profile.strategy.tier == StrategyTier.HEADLESS_PLUS_EVASION
    assert "https://www.washingtonpost.com/arcio/sitemap/index/" in profile.robots.sitemap_urls


def test_irs_like_drupal_on_akamai():
    home = {
        "url": "https://www.irs.gov/",
        "status": 200,
        "headers": {
            "x-generator": "Drupal 10 (https://www.drupal.org)",
            "x-drupal-dynamic-cache": "MISS",
        },
        "set_cookies": ["akaalb_DMAF_ALB_PROD=x", "_abck=y", "bm_sz=z"],
        "html": '<html><head><meta name="Generator" content="Drupal 10"></head><body>' + 'x' * 50_000 + '</body></html>',
    }
    pair = make_pair(home_kwargs=home)
    profile = profile_pair(pair)
    fw_names = [e.name for e in profile.framework]
    assert "drupal" in fw_names
    edge_names = [e.name for e in profile.edge]
    assert "akamai" in edge_names
    bp_names = [e.name for e in profile.bot_protection]
    assert "akamai_bot_manager" in bp_names
    # akamai BM is armed passive (200 OK) — should still get static_html
    assert profile.block_status == BlockStatus.ARMED_PASSIVE
    assert profile.strategy.tier in (StrategyTier.STATIC_HTML, StrategyTier.HEADLESS_RENDER)


def test_openai_like_app_router_on_vercel_behind_cf():
    html = '''<html data-dpl-id="dpl_abc">
<body>
<script>self.__next_f.push([1,"data"]);self.__next_f.push([2,"more"]);</script>
</body></html>'''
    home = {
        "url": "https://openai.com/",
        "status": 200,
        "headers": {
            "server": "cloudflare",
            "cf-ray": "abc",
            "x-vercel-cache": "HIT",
            "x-vercel-id": "fra1::pdx1::abc",
            "x-powered-by": "Next.js",
            "x-nextjs-prerender": "1",
            "vary": "rsc, next-router-state-tree, next-router-prefetch, next-router-segment-prefetch",
        },
        "set_cookies": ["__cf_bm=x", "_cfuvid=y"],
        "html": html,
    }
    pair = make_pair(home_kwargs=home)
    profile = profile_pair(pair)

    edge_names = [e.name for e in profile.edge]
    assert "cloudflare" in edge_names
    assert "vercel" in edge_names

    fw_names = [e.name for e in profile.framework]
    assert "next.js" in fw_names
    nextjs_ev = next(e for e in profile.framework if e.name == "next.js")
    assert "app_router" in nextjs_ev.extra.get("mode", "")

    blob_names = [b.name for b in profile.hydration_blobs]
    assert "self.__next_f" in blob_names

    assert profile.block_status == BlockStatus.ARMED_PASSIVE
    assert profile.strategy.tier == StrategyTier.HYDRATION_BLOB
