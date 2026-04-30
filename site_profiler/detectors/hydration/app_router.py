"""Detect Next.js App Router streaming RSC payload (self.__next_f.push)."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register_hydration
from ...schema import HydrationBlob


@register_hydration
def app_router_rsc(pair: FetchedPair) -> list[HydrationBlob]:
    home = pair.home
    if "self.__next_f.push" not in home.body_lower:
        return []
    count = home.body_lower.count("self.__next_f.push")
    return [HydrationBlob(name="self.__next_f", size_bytes=count, sample="App Router RSC stream")]
