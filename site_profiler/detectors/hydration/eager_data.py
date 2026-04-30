"""Detect Naver-style window['EAGER-DATA'] hydration object."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register_hydration
from ...schema import HydrationBlob


@register_hydration
def eager_data(pair: FetchedPair) -> list[HydrationBlob]:
    body = pair.home.body_lower
    if "eager-data" in body and ("window[" in body or "window." in body):
        return [HydrationBlob(name="EAGER-DATA", size_bytes=0, sample="Naver hydration global")]
    return []
