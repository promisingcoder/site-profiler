"""Shopify storefront detector + Shopify Hydrogen / Oxygen variants.

Variants on the ``shopify`` Evidence:
    - ``core``: classic Liquid storefront (cdn.shopify.com, _shopify_*
      cookies, ``Shopify.theme`` global).
    - ``hydrogen``: React-based storefront on Shopify's Oxygen runtime
      (``powered-by`` mentions Hydrogen).
    - ``oxygen``: Hydrogen apps deployed on Oxygen edge (``oxygen-*``
      headers). ``hydrogen`` and ``oxygen`` co-occur on Oxygen-hosted
      Hydrogen sites; they're separately detectable so a self-hosted
      Hydrogen app (rare) reports only ``hydrogen``.

We keep ``shopify_hydrogen`` as a separate Evidence too (legacy strategy
keys off the name); the variants give a finer-grained record without
breaking the existing strategy ranker.
"""
from __future__ import annotations

from ...parse import FetchedPair
from ...schema import Evidence, Variant
from ..base import BaseMatch, Detector, VariantProbe
from ...registry import register


class ShopifyCore(VariantProbe):
    name = "core"
    label = "Shopify (Liquid / Online Store)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        body = pair.home.body_lower
        if "shopify.theme" in body or "shopify.shop" in body or "shopify.routes" in body:
            markers.append("Shopify.theme/Shopify.shop/Shopify.routes globals")
        if any("cdn.shopify.com" in h for h in pair.home.script_src_hosts):
            markers.append("cdn.shopify.com script host")
        if any("/cdn/shopifycloud/" in s for s in pair.home.script_srcs):
            markers.append("/cdn/shopifycloud/ asset path")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.95, markers=markers)


class ShopifyHydrogen(VariantProbe):
    name = "hydrogen"
    label = "Shopify Hydrogen"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        powered_by = pair.home.header("powered-by").lower()
        if "hydrogen" in powered_by:
            markers.append(f"powered-by: {pair.home.header('powered-by')}")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.95, markers=markers)


class ShopifyOxygen(VariantProbe):
    name = "oxygen"
    label = "Shopify Oxygen (edge runtime)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        powered_by = pair.home.header("powered-by").lower()
        if "oxygen" in powered_by:
            markers.append(f"powered-by mentions Oxygen: {pair.home.header('powered-by')}")
        if pair.home.header("oxygen-full-page-cache"):
            markers.append("oxygen-full-page-cache header")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.95, markers=markers)


class Shopify(Detector):
    name = "shopify"
    category = "framework"
    base_confidence = 0.85
    variants = (ShopifyCore, ShopifyHydrogen, ShopifyOxygen)
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        home = pair.home
        markers: list[str] = []

        powered_by = home.header("powered-by")
        if "shopify" in powered_by.lower():
            markers.append(f"powered-by: {powered_by}")
        if home.header("shopify-complexity-score"):
            markers.append("shopify-complexity-score header")
        if home.header("x-shopify-stage") or home.header("x-shopid"):
            markers.append("x-shopify-stage / x-shopid header")

        shopify_cookies = [c for c in home.set_cookie_names if c.startswith("_shopify_")]
        if shopify_cookies:
            markers.append(f"shopify cookies: {shopify_cookies}")

        if any("cdn.shopify.com" in h for h in home.script_src_hosts):
            markers.append("cdn.shopify.com script host")
        if any("sdks.shopifycdn.com" in h for h in home.script_src_hosts):
            markers.append("sdks.shopifycdn.com script host")
        if any("/cdn/shopifycloud/" in s for s in home.script_srcs):
            markers.append("/cdn/shopifycloud/ asset path")

        body_lower = home.body_lower
        if "shopify.theme" in body_lower or "shopify.shop" in body_lower or "shopify.routes" in body_lower:
            markers.append("Shopify.theme/Shopify.shop/Shopify.routes globals")

        # myshopify.com domain in canonical / og:url
        for prop in ("og:url", "canonical"):
            v = home.metas.get(prop, "").lower()
            if ".myshopify.com" in v:
                markers.append(f"{prop}: {v}")

        for c in pair.robots_parsed.comments:
            if "shopify" in c.lower():
                markers.append(f"robots.txt comment: {c[:80]}")
                break

        if not markers:
            return BaseMatch()
        return BaseMatch(markers=markers)


shopify = Shopify._runner  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Legacy: keep the standalone shopify_hydrogen Evidence so strategy.py and
# downstream consumers that currently key on its name continue to work.
# When variants on the parent Shopify Evidence are everywhere consumed,
# this can be removed without further changes.
# ---------------------------------------------------------------------------


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
