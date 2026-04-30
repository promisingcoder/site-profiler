"""WordPress detector. Robust to enterprise variants that strip generator meta."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("framework")
def wordpress(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    robots = pair.robots
    markers: list[str] = []

    # Definitive: Link: <.../wp-json/>; rel="https://api.w.org/"
    link_h = home.header("link")
    if "api.w.org" in link_h.lower():
        markers.append("Link: rel=https://api.w.org/")

    # Cloudflare APO emits this for WP origins
    cf_edge = home.header("cf-edge-cache").lower()
    if "platform=wordpress" in cf_edge:
        markers.append(f"cf-edge-cache: {home.header('cf-edge-cache')}")

    # Generator meta — informative but easily stripped
    for g in home.meta_generators:
        if "wordpress" in g.lower() or "aioseo" in g.lower() or "yoast" in g.lower():
            markers.append(f"meta generator: {g}")

    # WPVIP-specific
    powered_by = home.header("x-powered-by").lower()
    if "wordpress vip" in powered_by:
        markers.append(f"x-powered-by: {home.header('x-powered-by')}")

    # X-Pingback
    if home.header("x-pingback"):
        markers.append("x-pingback header")

    # Body markers
    body_lower = home.body_lower
    if body_lower.count("wp-content/") >= 5:
        markers.append(f"wp-content/ paths in body (~{body_lower.count('wp-content/')} hits)")
    if body_lower.count("wp-includes/") >= 3:
        markers.append("wp-includes/ paths in body")
    if "wp-block-" in body_lower:
        markers.append("wp-block-* class names")

    # Robots.txt non-standard "Schemamap:" directive pointing to wp-json
    for k, vals in pair.robots_parsed.nonstandard_directives.items():
        for v in vals:
            if "wp-json" in v.lower():
                markers.append(f"robots.txt {k}: {v}")
                break

    if "wp_ak_" in " ".join(home.set_cookie_names + robots.set_cookie_names):
        markers.append("wp_ak_* cookies (WP behind Akamai)")

    if not markers:
        return None
    confidence = 0.95 if len(markers) >= 2 else 0.8
    return Evidence(name="wordpress", confidence=confidence, markers=markers)
