"""Next.js framework detector — covers Pages Router, App Router, and header-only variants."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("framework")
def nextjs(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []
    modes: set[str] = set()

    # Header-only signals
    powered_by = home.header("x-powered-by")
    if "next.js" in powered_by.lower():
        markers.append(f"x-powered-by: {powered_by}")
        modes.add("header")
    for h in ("x-nextjs-prerender", "x-nextjs-cache", "x-nextjs-stale-time"):
        if home.header(h):
            markers.append(f"{h} header")
            modes.add("header")
    if home.header("x-matched-path"):
        markers.append(f"x-matched-path: {home.header('x-matched-path')}")
        modes.add("header")

    # App Router via Vary
    vary = home.header("vary").lower()
    if "rsc" in vary and "next-router-state-tree" in vary:
        markers.append(f"vary: {home.header('vary')}")
        modes.add("app_router")

    # Pages Router via __NEXT_DATA__ JSON island
    next_data_islands = [i for i in home.named_json_islands if i[0] == "__NEXT_DATA__"]
    if next_data_islands:
        sid, _t, size, _sample = next_data_islands[0]
        markers.append(f"<script id=__NEXT_DATA__> ({size} bytes)")
        modes.add("pages_router")

    # App Router via streaming RSC
    if "self.__next_f.push" in home.body_lower:
        count = home.body_lower.count("self.__next_f.push")
        markers.append(f"self.__next_f.push x{count} (App Router RSC stream)")
        modes.add("app_router")

    # Static asset path hint
    has_next_static = any("/_next/static/" in s for s in home.script_srcs)
    if has_next_static:
        markers.append("/_next/static/ asset paths")

    if not markers:
        return None

    confidence = 0.99 if len(modes) >= 1 and (next_data_islands or modes.intersection({"app_router"}) or has_next_static) else 0.85
    extra = {"mode": ",".join(sorted(modes))} if modes else {}
    return Evidence(name="next.js", confidence=confidence, markers=markers, extra=extra)
