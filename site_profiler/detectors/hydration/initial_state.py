"""Detect window.__INITIAL_STATE__ Redux-style hydration."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register_hydration
from ...schema import HydrationBlob


@register_hydration
def initial_state(pair: FetchedPair) -> list[HydrationBlob]:
    body = pair.home.body_lower
    out: list[HydrationBlob] = []
    if "window.__initial_state__" in body or "__initial_state__=" in body:
        out.append(HydrationBlob(name="__INITIAL_STATE__", size_bytes=0, sample="Redux-style state"))
    if "window.__apollo_state__" in body:
        out.append(HydrationBlob(name="__APOLLO_STATE__", size_bytes=0, sample="Apollo client state"))
    if "window.__preloadeddata" in body:
        out.append(HydrationBlob(name="__preloadedData", size_bytes=0, sample="NYT-style preloaded data"))
    return out
