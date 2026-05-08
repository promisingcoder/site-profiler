"""Magento (Adobe Commerce) detector — Magento 1 vs Magento 2 as variants.

Magento 1 markers:
    - ``js/mage`` script paths,
    - ``skin/frontend/`` asset paths (with ``enterprise`` substring → Enterprise edition),
    - global ``Mage`` / ``VarienForm``.

Magento 2 markers:
    - ``static/_requirejs`` paths,
    - ``<script type="text/x-magento-init">`` blocks,
    - ``data-requiremodule="mage/..."`` / ``Magento_*``,
    - cookies ``X-Magento-Vary``, ``mage-cache-storage``.
"""
from __future__ import annotations

from ...parse import FetchedPair
from ...schema import Variant
from ..base import BaseMatch, Detector, VariantProbe


class MagentoV1(VariantProbe):
    name = "v1"
    label = "Magento 1.x"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        body = pair.home.body_lower
        if "js/mage/" in body or "/js/mage." in body:
            markers.append("js/mage/ asset path (Magento 1)")
        if "skin/frontend/enterprise" in body:
            markers.append("skin/frontend/enterprise (Magento 1 Enterprise edition)")
        elif "skin/frontend/default" in body or "skin/frontend/base" in body:
            markers.append("skin/frontend/ (Magento 1 Community edition)")
        if "varienform" in body:
            markers.append("VarienForm global")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.9, markers=markers)


class MagentoV2(VariantProbe):
    name = "v2"
    label = "Magento 2.x / Adobe Commerce"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        body = pair.home.body_lower
        if "static/_requirejs" in body or "/static/version" in body:
            markers.append("static/_requirejs path (Magento 2)")
        if 'type="text/x-magento-init"' in body:
            markers.append('<script type="text/x-magento-init">')
        if "data-requiremodule=\"mage/" in body or "data-requiremodule=\"magento_" in body:
            markers.append("data-requiremodule=Mage/Magento_* (Magento 2)")
        # Substring match — covers `mage-cache-storage`,
        # `mage-cache-storage-section-invalidation`, `mage-translation-storage`,
        # and any other mage-cache-* / mage-translation-* siblings.
        for c in pair.home.set_cookie_names:
            cl = c.lower()
            if "mage-cache-storage" in cl or "mage-translation-storage" in cl:
                markers.append(f"cookie: {c}")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.95, markers=markers)


class Magento(Detector):
    name = "magento"
    category = "framework"
    base_confidence = 0.85
    variants = (MagentoV1, MagentoV2)
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        markers: list[str] = []
        body = pair.home.body_lower
        cookies = [c.lower() for c in pair.home.set_cookie_names]
        if any(c.startswith("x-magento-vary") for c in cookies):
            markers.append("X-Magento-Vary cookie")
        for c in cookies:
            if c.startswith("mage-") or c.startswith("magento-"):
                markers.append(f"cookie: {c}")
                break
        if "js/mage" in body or "static/_requirejs" in body:
            markers.append("Magento asset paths in body")
        if 'type="text/x-magento-init"' in body:
            markers.append('<script type="text/x-magento-init"> block')
        if not markers:
            return BaseMatch()
        return BaseMatch(markers=markers)
