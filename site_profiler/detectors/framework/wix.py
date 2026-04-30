"""Wix detector. Avoids the substring-match false-positive trap (kayak ID strings contained 'wix')."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("framework")
def wix(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    for host in home.script_src_hosts:
        h = host.lower()
        if "parastorage.com" in h or "wixstatic.com" in h or "wix.com" in h:
            markers.append(f"script host: {host}")

    for g in home.meta_generators:
        if g.lower().startswith("wix.com") or "wix " in g.lower():
            markers.append(f"meta generator: {g}")

    if "_wixCIDX" in home.set_cookie_names:
        markers.append("_wixCIDX cookie")

    if not markers:
        return None
    confidence = 0.95 if len(markers) >= 2 else 0.8
    return Evidence(name="wix", confidence=confidence, markers=markers)
