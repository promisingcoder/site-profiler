"""Shopify storefront detector + Shopify Hydrogen detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


def _shopify_markers(pair: FetchedPair) -> list[str]:
    home = pair.home
    markers: list[str] = []

    powered_by = home.header("powered-by")
    if "shopify" in powered_by.lower():
        markers.append(f"powered-by: {powered_by}")
    if home.header("shopify-complexity-score"):
        markers.append("shopify-complexity-score header")

    shopify_cookies = [c for c in home.set_cookie_names if c.startswith("_shopify_")]
    if shopify_cookies:
        markers.append(f"shopify cookies: {shopify_cookies}")

    if any("cdn.shopify.com" in h for h in home.script_src_hosts):
        markers.append("cdn.shopify.com script host")

    body_lower = home.body_lower
    if "shopify.theme" in body_lower or "shopify.shop" in body_lower or "shopify.routes" in body_lower:
        markers.append("Shopify.theme/Shopify.shop/Shopify.routes globals")

    # robots.txt comment / disallow patterns
    for c in pair.robots_parsed.comments:
        if "shopify" in c.lower():
            markers.append(f"robots.txt comment: {c[:80]}")
            break

    if any("/cdn/shopifycloud/" in s for s in home.script_srcs):
        markers.append("/cdn/shopifycloud/ asset path")

    return markers


@register("framework")
def shopify(pair: FetchedPair) -> Evidence | None:
    markers = _shopify_markers(pair)
    if not markers:
        return None
    confidence = 0.99 if len(markers) >= 2 else 0.85
    return Evidence(name="shopify", confidence=confidence, markers=markers)


@register("framework")
def shopify_hydrogen(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    powered_by = home.header("powered-by").lower()
    if "hydrogen" in powered_by:
        markers.append(f"powered-by: {home.header('powered-by')}")
    if "oxygen" in powered_by:
        markers.append(f"powered-by mentions Oxygen: {home.header('powered-by')}")
    if home.header("oxygen-full-page-cache"):
        markers.append("oxygen-full-page-cache header")

    if not markers:
        return None
    return Evidence(name="shopify_hydrogen", confidence=0.95, markers=markers)
