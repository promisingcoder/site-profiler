"""Public API: profile_url and profile_pair."""
from __future__ import annotations

from .aggregate import aggregate
from .fetch import CHROME_UA, DEFAULT_MAX_BODY, DEFAULT_TIMEOUT, fetch_pair
from .parse import FetchedPair
from .schema import SiteProfile


def profile_url(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_body_bytes: int = DEFAULT_MAX_BODY,
    user_agent: str = CHROME_UA,
) -> SiteProfile:
    """Fetch URL + /robots.txt and return a SiteProfile."""
    pair = fetch_pair(
        url,
        timeout=timeout,
        max_body_bytes=max_body_bytes,
        user_agent=user_agent,
    )
    return aggregate(pair)


def profile_pair(pair: FetchedPair) -> SiteProfile:
    """Profile from an already-built FetchedPair (useful for testing or replay)."""
    return aggregate(pair)
