from site_profiler.schema import (
    BlockStatus,
    Evidence,
    HydrationBlob,
    StrategyTier,
    StructuredData,
)
from site_profiler.strategy import rank_strategy


def test_blocked_routes_to_evasion():
    s = rank_strategy(
        block_status=BlockStatus.SOFT_CHALLENGE,
        framework=[Evidence(name="next.js", confidence=0.99, markers=[])],
        hydration_blobs=[HydrationBlob(name="__NEXT_DATA__", size_bytes=1000)],
        structured=StructuredData(),
        body_size=10_000,
    )
    assert s.tier == StrategyTier.HEADLESS_PLUS_EVASION


def test_hard_block_routes_to_evasion():
    s = rank_strategy(
        block_status=BlockStatus.HARD_BLOCK,
        framework=[],
        hydration_blobs=[],
        structured=StructuredData(),
        body_size=0,
    )
    assert s.tier == StrategyTier.HEADLESS_PLUS_EVASION


def test_body_lies_routes_to_evasion():
    s = rank_strategy(
        block_status=BlockStatus.BODY_LIES,
        framework=[],
        hydration_blobs=[],
        structured=StructuredData(),
        body_size=2000,
    )
    assert s.tier == StrategyTier.HEADLESS_PLUS_EVASION


def test_shopify_routes_to_api_direct():
    s = rank_strategy(
        block_status=BlockStatus.NONE,
        framework=[Evidence(name="shopify", confidence=0.99, markers=[])],
        hydration_blobs=[],
        structured=StructuredData(),
        body_size=50_000,
    )
    assert s.tier == StrategyTier.API_DIRECT


def test_shopify_armed_passive_still_api_direct():
    s = rank_strategy(
        block_status=BlockStatus.ARMED_PASSIVE,
        framework=[Evidence(name="shopify", confidence=0.99, markers=[])],
        hydration_blobs=[],
        structured=StructuredData(),
        body_size=50_000,
    )
    assert s.tier == StrategyTier.API_DIRECT


def test_wordpress_routes_to_api_direct():
    s = rank_strategy(
        block_status=BlockStatus.NONE,
        framework=[Evidence(name="wordpress", confidence=0.95, markers=[])],
        hydration_blobs=[],
        structured=StructuredData(),
        body_size=50_000,
    )
    assert s.tier == StrategyTier.API_DIRECT


def test_next_data_routes_to_hydration_blob():
    s = rank_strategy(
        block_status=BlockStatus.NONE,
        framework=[Evidence(name="next.js", confidence=0.99, markers=[])],
        hydration_blobs=[HydrationBlob(name="__NEXT_DATA__", size_bytes=1000)],
        structured=StructuredData(),
        body_size=50_000,
    )
    assert s.tier == StrategyTier.HYDRATION_BLOB


def test_static_html_via_json_ld():
    s = rank_strategy(
        block_status=BlockStatus.NONE,
        framework=[],
        hydration_blobs=[],
        structured=StructuredData(json_ld_present=True, json_ld_types=["Organization"]),
        body_size=50_000,
    )
    assert s.tier == StrategyTier.STATIC_HTML


def test_static_html_via_microdata():
    s = rank_strategy(
        block_status=BlockStatus.NONE,
        framework=[],
        hydration_blobs=[],
        structured=StructuredData(microdata=True, microdata_types=["Product"]),
        body_size=50_000,
    )
    assert s.tier == StrategyTier.STATIC_HTML


def test_small_body_no_data_routes_to_headless_render():
    s = rank_strategy(
        block_status=BlockStatus.NONE,
        framework=[],
        hydration_blobs=[],
        structured=StructuredData(),
        body_size=8_000,
    )
    assert s.tier == StrategyTier.HEADLESS_RENDER
