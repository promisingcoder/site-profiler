"""Next.js framework detector — Pages Router, App Router, header-only.

Variants:
    - ``pages_router``: ``<script id="__NEXT_DATA__">`` JSON island present.
      Old-school SSG/SSR mode; props live in a single hydration blob.
    - ``app_router``: ``self.__next_f.push(...)`` calls in body, or response
      ``Vary: rsc, next-router-state-tree``. Streaming RSC; data is spread
      across many small islands.
    - ``header_only``: only ``x-powered-by: Next.js`` / ``x-nextjs-*`` —
      typically RSC-only with the streaming chunks elided from the initial
      doc, or the render is gated behind auth.

Version capture: ``x-powered-by: Next.js ([0-9.]+)`` (Wappalyzer pattern;
modern Next on Vercel sends just ``Next.js`` without a version, so this is
opportunistic).
"""
from __future__ import annotations

import re

from ...parse import FetchedPair
from ...schema import Variant
from ..base import BaseMatch, Detector, VariantProbe


_VERSION_RE = re.compile(r"next\.js\s*v?([0-9]+\.[0-9]+(?:\.[0-9]+)?)", re.I)


class NextJsPagesRouter(VariantProbe):
    name = "pages_router"
    label = "Next.js Pages Router"

    def probe(self, pair: FetchedPair) -> Variant | None:
        islands = [i for i in pair.home.named_json_islands if i[0] == "__NEXT_DATA__"]
        if not islands:
            return None
        sid, _t, size, _sample = islands[0]
        return Variant(
            name=self.name,
            label=self.label,
            confidence=0.99,
            markers=[f"<script id={sid}> ({size} bytes)"],
        )


class NextJsAppRouter(VariantProbe):
    name = "app_router"
    label = "Next.js App Router"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        body = pair.home.body_lower
        if "self.__next_f.push" in body:
            count = body.count("self.__next_f.push")
            markers.append(f"self.__next_f.push x{count} (App Router RSC stream)")
        vary = pair.home.header("vary").lower()
        if "rsc" in vary and "next-router-state-tree" in vary:
            markers.append(f"vary: {pair.home.header('vary')}")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.99, markers=markers)


class NextJsHeaderOnly(VariantProbe):
    """Only matches if there's no Pages Router data and no App Router stream
    — i.e. we know it's Next.js but can't tell which router from the body."""
    name = "header_only"
    label = "Next.js (header-only — router unknown)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        body = pair.home.body_lower
        has_pages = any(i[0] == "__NEXT_DATA__" for i in pair.home.named_json_islands)
        has_app = "self.__next_f.push" in body or (
            "rsc" in pair.home.header("vary").lower()
            and "next-router-state-tree" in pair.home.header("vary").lower()
        )
        if has_pages or has_app:
            return None
        markers: list[str] = []
        powered_by = pair.home.header("x-powered-by")
        if "next.js" in powered_by.lower():
            markers.append(f"x-powered-by: {powered_by}")
        for h in ("x-nextjs-prerender", "x-nextjs-cache", "x-nextjs-stale-time", "x-matched-path"):
            if pair.home.header(h):
                markers.append(f"{h} header")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.85, markers=markers)


class NextJs(Detector):
    name = "next.js"
    category = "framework"
    base_confidence = 0.9
    variants = (NextJsPagesRouter, NextJsAppRouter, NextJsHeaderOnly)
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        markers: list[str] = []
        modes: set[str] = set()

        powered_by = pair.home.header("x-powered-by")
        if "next.js" in powered_by.lower():
            markers.append(f"x-powered-by: {powered_by}")
            modes.add("header")
        for h in ("x-nextjs-prerender", "x-nextjs-cache", "x-nextjs-stale-time"):
            if pair.home.header(h):
                markers.append(f"{h} header")
                modes.add("header")
        if pair.home.header("x-matched-path"):
            markers.append(f"x-matched-path: {pair.home.header('x-matched-path')}")
            modes.add("header")

        vary = pair.home.header("vary").lower()
        if "rsc" in vary and "next-router-state-tree" in vary:
            markers.append(f"vary: {pair.home.header('vary')}")
            modes.add("app_router")

        next_data_islands = [i for i in pair.home.named_json_islands if i[0] == "__NEXT_DATA__"]
        if next_data_islands:
            sid, _t, size, _sample = next_data_islands[0]
            markers.append(f"<script id={sid}> ({size} bytes)")
            modes.add("pages_router")

        body = pair.home.body_lower
        if "self.__next_f.push" in body:
            count = body.count("self.__next_f.push")
            markers.append(f"self.__next_f.push x{count}")
            modes.add("app_router")

        has_next_static = any("/_next/static/" in s for s in pair.home.script_srcs)
        if has_next_static:
            markers.append("/_next/static/ asset paths")

        if not markers:
            return BaseMatch()

        extra = {"mode": ",".join(sorted(modes))} if modes else {}

        # Version capture — try x-powered-by first, then meta generator
        version = None
        m = _VERSION_RE.search(powered_by)
        if m:
            version = m.group(1)
        if version is None:
            for g in pair.home.meta_generators:
                m = _VERSION_RE.search(g)
                if m:
                    version = m.group(1)
                    break

        return BaseMatch(markers=markers, extra=extra, version=version)


nextjs = NextJs._runner  # type: ignore[attr-defined]
