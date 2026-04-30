"""AWS CloudFront edge detector."""
from __future__ import annotations

from ...parse import FetchedPair
from ...registry import register
from ...schema import Evidence


@register("edge")
def cloudfront(pair: FetchedPair) -> Evidence | None:
    home = pair.home
    markers: list[str] = []

    if "cloudfront" in home.header("server").lower():
        markers.append(f"server: {home.header('server')}")
    via = home.header("via").lower()
    if "cloudfront.net" in via:
        markers.append(f"via: {home.header('via')}")
    if home.header("x-amz-cf-id"):
        markers.append("x-amz-cf-id header")
    if home.header("x-amz-cf-pop"):
        markers.append(f"x-amz-cf-pop: {home.header('x-amz-cf-pop')}")
    x_cache = home.header("x-cache").lower()
    if "from cloudfront" in x_cache:
        markers.append(f"x-cache: {home.header('x-cache')}")

    if not markers:
        return None
    confidence = 0.99 if len(markers) >= 2 else 0.85
    return Evidence(name="cloudfront", confidence=confidence, markers=markers)
