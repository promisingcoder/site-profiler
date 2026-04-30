"""Deterministic strategy ranker."""
from __future__ import annotations

from .schema import (
    BlockStatus,
    Evidence,
    HydrationBlob,
    Strategy,
    StrategyTier,
    StructuredData,
)

BLOCKED_STATES = {
    BlockStatus.SOFT_CHALLENGE,
    BlockStatus.HARD_BLOCK,
    BlockStatus.BODY_LIES,
    BlockStatus.TLS_BLOCK,
}

# Frameworks that always server-render in plain HTML — strong signal for static_html
# regardless of body size or structured-data presence.
STATIC_RENDERED_FRAMEWORKS = {
    "sphinx",
    "ghost",
    "drupal",
    "salesforce_pbc",
    "hubspot",
    "webflow",
}


def rank_strategy(
    *,
    block_status: BlockStatus,
    framework: list[Evidence],
    hydration_blobs: list[HydrationBlob],
    structured: StructuredData,
    body_size: int,
) -> Strategy:
    fw_names = {e.name for e in framework}
    evidence: list[str] = []

    if block_status in BLOCKED_STATES:
        evidence.append(f"block_status={block_status.value}")
        return Strategy(
            tier=StrategyTier.HEADLESS_PLUS_EVASION,
            confidence=0.95,
            evidence=evidence,
        )

    api_direct_frameworks = {
        "shopify",
        "shopify_hydrogen",
        "wordpress",
    }
    api_hits = api_direct_frameworks & fw_names
    if api_hits:
        if "shopify" in api_hits or "shopify_hydrogen" in api_hits:
            evidence.append("Shopify storefront detected; /products.json likely public")
        if "wordpress" in api_hits:
            evidence.append("WordPress detected; /wp-json/wp/v2/* likely public")
        return Strategy(
            tier=StrategyTier.API_DIRECT,
            confidence=0.85,
            evidence=evidence,
        )

    if hydration_blobs:
        names = ", ".join(b.name for b in hydration_blobs)
        evidence.append(f"hydration blobs in initial HTML: {names}")
        return Strategy(
            tier=StrategyTier.HYDRATION_BLOB,
            confidence=0.85,
            evidence=evidence,
        )

    static_fw_hits = STATIC_RENDERED_FRAMEWORKS & fw_names
    if static_fw_hits:
        evidence.append(
            f"server-rendered framework: {sorted(static_fw_hits)}"
        )
        return Strategy(
            tier=StrategyTier.STATIC_HTML,
            confidence=0.85,
            evidence=evidence,
        )

    if structured.json_ld_present or structured.microdata:
        if structured.json_ld_present:
            types = ", ".join(structured.json_ld_types[:5]) or "(types unknown)"
            evidence.append(f"JSON-LD present: {types}")
        if structured.microdata:
            mt = ", ".join(structured.microdata_types[:5]) or "(types unknown)"
            evidence.append(f"schema.org microdata present: {mt}")
        return Strategy(
            tier=StrategyTier.STATIC_HTML,
            confidence=0.7,
            evidence=evidence,
        )

    if body_size > 10_000:
        evidence.append(
            f"server-rendered HTML (~{body_size} bytes), no hydration blob, no structured data; selectors needed"
        )
        return Strategy(
            tier=StrategyTier.STATIC_HTML,
            confidence=0.55,
            evidence=evidence,
        )

    evidence.append(
        f"small body ({body_size} bytes), no hydration blob, no structured data; likely SPA shell"
    )
    return Strategy(
        tier=StrategyTier.HEADLESS_RENDER,
        confidence=0.6,
        evidence=evidence,
    )
