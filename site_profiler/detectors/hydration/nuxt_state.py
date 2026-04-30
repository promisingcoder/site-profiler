"""Detect Nuxt.js __NUXT__ hydration global."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register_hydration
from ...schema import HydrationBlob


@register_hydration
def nuxt_state(pair: FetchedPair) -> list[HydrationBlob]:
    body = pair.home.body_lower
    if "window.__nuxt__" in body or "__nuxt__=" in body:
        return [HydrationBlob(name="__NUXT__", size_bytes=0, sample="Nuxt state global")]
    return []
