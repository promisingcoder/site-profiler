"""Detect generic <script id="..." type="application/json"> JSON islands.

Catches Stubhub's <script id="app-context"> and similar custom hydration approaches.
Only reports islands with non-trivial size to avoid noise.
"""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register_hydration
from ...schema import HydrationBlob

_KNOWN_NAMES = {"__NEXT_DATA__"}  # already covered by next_data.py


@register_hydration
def app_context(pair: FetchedPair) -> list[HydrationBlob]:
    out: list[HydrationBlob] = []
    for sid, type_attr, size, sample in pair.home.named_json_islands:
        if sid in _KNOWN_NAMES:
            continue
        if size < 200:
            continue
        out.append(HydrationBlob(name=sid, size_bytes=size, sample=sample))
    return out
