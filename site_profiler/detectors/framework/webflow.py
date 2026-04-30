"""Webflow detector. Recon found x-wf-* headers + cdn.prod.website-files.com host."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("framework")
def webflow(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for h in home.headers_lc:
        if h.startswith("x-wf-"):
            markers.append(f"{h} header")

    for host in home.script_src_hosts:
        if "website-files.com" in host or "webflow.com" in host:
            markers.append(f"script host: {host}")

    for g in home.meta_generators:
        if "webflow" in g.lower():
            markers.append(f"meta generator: {g}")

    # data-wf-* attributes on html/body
    for attrs in (home.html_attrs, home.body_attrs):
        for k in attrs:
            if k.startswith("data-wf-"):
                markers.append(f"{k} attribute on root tag")
                break

    if not markers:
        return None
    confidence = 0.9 if len(markers) >= 2 else 0.75
    return Evidence(name="webflow", confidence=confidence, markers=markers)
