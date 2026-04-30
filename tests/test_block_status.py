from site_profiler.block_status import compute_block_status
from site_profiler.schema import BlockStatus

from .conftest import make_pair


def test_clean_200_is_none():
    pair = make_pair(home_kwargs={
        "status": 200,
        "html": "<html><body>" + "x" * 10_000 + "</body></html>",
    })
    s, _ = compute_block_status(pair)
    assert s == BlockStatus.NONE


def test_armed_passive_with_cf_bm():
    pair = make_pair(home_kwargs={
        "status": 200,
        "html": "<html><body>real content " + "x" * 10_000 + "</body></html>",
        "set_cookies": ["__cf_bm=xyz", "_cfuvid=abc"],
    })
    s, ev = compute_block_status(pair)
    assert s == BlockStatus.ARMED_PASSIVE
    assert any("__cf_bm" in m for m in ev)


def test_cf_mitigated_challenge_is_soft():
    pair = make_pair(home_kwargs={
        "status": 403,
        "html": "<html><body>blocked</body></html>",
        "headers": {"cf-mitigated": "challenge"},
    })
    s, _ = compute_block_status(pair)
    assert s == BlockStatus.SOFT_CHALLENGE


def test_aws_waf_captcha_405_is_soft():
    pair = make_pair(home_kwargs={
        "status": 405,
        "html": "<html><body>captcha</body></html>",
        "headers": {"x-amzn-waf-action": "captcha"},
    })
    s, _ = compute_block_status(pair)
    assert s == BlockStatus.SOFT_CHALLENGE


def test_tls_block_when_home_failed_and_robots_ok():
    pair = make_pair(
        home_kwargs={"status": None, "fetch_error": "ConnectError: TLS reset", "html": ""},
        robots_kwargs={"status": 200, "html": "Sitemap: https://example.com/s.xml\n"},
    )
    s, _ = compute_block_status(pair)
    assert s == BlockStatus.TLS_BLOCK


def test_tiktok_style_200_with_waf_body_lies():
    pair = make_pair(home_kwargs={
        "status": 200,
        "html": '<html><body class="_wafchallengeid">please wait</body></html>',
        "headers": {"content-type": "text/html"},
    })
    s, _ = compute_block_status(pair)
    assert s == BlockStatus.BODY_LIES


def test_akamai_42_byte_stub():
    pair = make_pair(home_kwargs={
        "status": 200,
        "html": "Reference  #18.187e19b8\n",
        "headers": {"server": "AkamaiNetStorage"},
    })
    s, _ = compute_block_status(pair)
    assert s == BlockStatus.BODY_LIES


def test_booking_202_aws_waf_js_challenge():
    pair = make_pair(home_kwargs={
        "status": 202,
        "html": '<html><body>Please wait... awsWafCookieDomainList...</body></html>',
        "headers": {"content-type": "text/html"},
    })
    s, _ = compute_block_status(pair)
    assert s == BlockStatus.SOFT_CHALLENGE


def test_hard_block_403_no_body():
    pair = make_pair(home_kwargs={
        "status": 403,
        "html": "x",
        "headers": {"server": "AkamaiGHost"},
    })
    s, _ = compute_block_status(pair)
    assert s == BlockStatus.HARD_BLOCK
