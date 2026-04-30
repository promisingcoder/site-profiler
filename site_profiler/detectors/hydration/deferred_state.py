"""Detect Airbnb Hyperloop's data-deferred-state-N JSON islands."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register_hydration
from ...schema import HydrationBlob


@register_hydration
def deferred_state(pair: FetchedPair) -> list[HydrationBlob]:
    body = pair.home.body_lower
    if "data-deferred-state-" in body:
        count = body.count("data-deferred-state-")
        return [HydrationBlob(name="data-deferred-state", size_bytes=count, sample="Airbnb Hyperloop deferred state")]
    return []
