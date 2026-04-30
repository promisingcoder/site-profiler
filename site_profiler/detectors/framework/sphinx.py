"""Sphinx (Python docs / many tech docs) detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("framework")
def sphinx(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for g in home.meta_generators:
        if g.lower().startswith("sphinx"):
            markers.append(f"meta generator: {g}")
            break

    body_lower = home.body_lower
    if "sphinxsidebar" in body_lower or "sphinx_highlight.js" in body_lower:
        markers.append("sphinxsidebar / sphinx_highlight.js")
    if "sphinx-doc.org" in body_lower:
        markers.append("sphinx-doc.org backlink")

    if not markers:
        return None
    confidence = 0.95 if len(markers) >= 2 else 0.8
    return Evidence(name="sphinx", confidence=confidence, markers=markers)
