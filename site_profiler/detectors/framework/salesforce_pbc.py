"""Salesforce.com's in-house 'PBC on Nunjucks' renderer."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("framework")
def salesforce_pbc(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    if "nunjuckspbc" in home.header("x-sfdc-page-render-type").lower():
        markers.append(f"x-sfdc-page-render-type: {home.header('x-sfdc-page-render-type')}")

    for g in home.meta_generators:
        if "pbc on nunjucks" in g.lower():
            markers.append(f"meta generator: {g}")

    for h in home.headers_lc:
        if h.startswith("x-sfdc-"):
            markers.append(f"{h} header")
            break

    if not markers:
        return None
    return Evidence(name="salesforce_pbc", confidence=0.9, markers=markers)
