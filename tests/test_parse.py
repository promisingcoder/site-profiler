from site_profiler.parse import (
    parse_body,
    parse_csp,
    parse_robots,
    parse_server_timing,
    parse_set_cookies,
)


def test_parse_csp_basic():
    csp = parse_csp(
        "default-src 'self'; script-src 'self' https://js.hcaptcha.com https://challenges.cloudflare.com;"
    )
    assert "script-src" in csp
    assert "https://js.hcaptcha.com" in csp["script-src"]
    assert "https://challenges.cloudflare.com" in csp["script-src"]


def test_parse_server_timing():
    st = parse_server_timing('cdn-cache; desc=HIT, ak_p; desc="0.1cc1645f"')
    names = [n for n, _ in st]
    assert "cdn-cache" in names
    assert "ak_p" in names


def test_parse_set_cookies_dedup_first_seen():
    headers = ["_shopify_y=abc; Path=/", "__cf_bm=xyz; Secure", "_shopify_y=def; Path=/"]
    names, values = parse_set_cookies(headers)
    assert names == ["_shopify_y", "__cf_bm"]
    assert values["_shopify_y"] == "abc"


def test_parse_robots_with_nonstandard_directive_and_comments():
    text = """# we use Shopify as our ecommerce platform
User-agent: *
Disallow: /admin/
Crawl-delay: 4
Sitemap: https://example.com/sitemap.xml
Schemamap: https://example.com/wp-json/yoast/v1/schema-aggregator
"""
    r = parse_robots(text)
    assert r["sitemap_urls"] == ["https://example.com/sitemap.xml"]
    assert r["crawl_delay"] == 4.0
    assert "schemamap" in r["nonstandard_directives"]
    assert any("Shopify" in c for c in r["comments"])
    assert not r["has_disallow_all"]


def test_parse_robots_disallow_all():
    text = "User-agent: *\nDisallow: /\n"
    r = parse_robots(text)
    assert r["has_disallow_all"]


def test_json_ld_requires_schema_org_context():
    # Naver-style false-positive trap: @type:"BLOCK" but no schema.org context
    bad = '<html><head><script type="application/json">{"@type":"BLOCK"}</script></head></html>'
    p = parse_body(bad)
    assert p["json_ld_blocks"] == []
    assert p["json_ld_types"] == []

    good = (
        '<html><head>'
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"Organization"}'
        '</script></head></html>'
    )
    p = parse_body(good)
    assert "Organization" in p["json_ld_types"]


def test_parse_body_metas_and_scripts():
    html = """<html lang="en">
<head>
<title>Test Page</title>
<meta name="generator" content="WordPress 6.0">
<meta property="og:title" content="x">
<meta name="twitter:card" content="summary">
<link rel="canonical" href="https://example.com/">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization"}</script>
</head>
<body>
<script src="https://cdn.shopify.com/x.js"></script>
<script>self.__next_f.push([1,"data"]);</script>
</body>
</html>"""
    p = parse_body(html)
    assert p["title"] == "Test Page"
    assert "WordPress 6.0" in p["meta_generators"]
    assert p["has_opengraph"] is True
    assert p["has_twitter_cards"] is True
    assert "Organization" in p["json_ld_types"]
    assert "cdn.shopify.com" in p["script_src_hosts"]


def test_named_json_island():
    html = (
        '<html><body>'
        '<script id="__NEXT_DATA__" type="application/json">{"buildId":"abc","props":{}}</script>'
        '</body></html>'
    )
    p = parse_body(html)
    ids = [i[0] for i in p["named_json_islands"]]
    assert "__NEXT_DATA__" in ids


def test_microdata_detection():
    html = '<html><body><div itemscope itemtype="https://schema.org/Product"><span itemprop="name">x</span></div></body></html>'
    p = parse_body(html)
    assert p["has_microdata"]
    assert "Product" in p["microdata_types"]
