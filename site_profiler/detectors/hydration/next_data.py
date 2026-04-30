"""Detect Next.js Pages Router __NEXT_DATA__ JSON island."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register_hydration
from ...schema import HydrationBlob


@register_hydration
def next_data(pair: FetchedPair) -> list[HydrationBlob]:
    out: list[HydrationBlob] = []
    for sid, _t, size, sample in pair.home.named_json_islands:
        if sid == "__NEXT_DATA__":
            out.append(HydrationBlob(name="__NEXT_DATA__", size_bytes=size, sample=sample))
    return out
