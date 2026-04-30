"""Sync httpx fetcher: homepage + /robots.txt with shared session."""
from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

import httpx

from .parse import FetchedPair, build_pair

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": CHROME_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

DEFAULT_TIMEOUT = 20.0
DEFAULT_MAX_BODY = 5_000_000


def fetch_pair(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_body_bytes: int = DEFAULT_MAX_BODY,
    user_agent: str = CHROME_UA,
) -> FetchedPair:
    """Two-probe sync fetch: homepage + /robots.txt."""
    home = _fetch_one(
        url,
        timeout=timeout,
        max_body_bytes=max_body_bytes,
        user_agent=user_agent,
    )
    robots_target = home["final_url"] or url
    robots_url = _robots_url_for(robots_target)
    robots = _fetch_one(
        robots_url,
        timeout=min(timeout, 8.0),
        max_body_bytes=200_000,
        user_agent=user_agent,
        accept="text/plain,*/*;q=0.5",
    )
    return build_pair(home, robots)


def _fetch_one(
    url: str,
    *,
    timeout: float,
    max_body_bytes: int,
    user_agent: str,
    accept: str | None = None,
) -> dict:
    headers = dict(DEFAULT_HEADERS)
    headers["User-Agent"] = user_agent
    if accept:
        headers["Accept"] = accept

    redirect_chain: list[tuple[int, str]] = []
    set_cookie_headers: list[str] = []
    try:
        with httpx.Client(
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
            max_redirects=10,
            http2=False,
        ) as client:
            resp = client.get(url)
            for h in resp.history:
                redirect_chain.append((h.status_code, str(h.url)))
                set_cookie_headers.extend(h.headers.get_list("set-cookie"))
            redirect_chain.append((resp.status_code, str(resp.url)))
            set_cookie_headers.extend(resp.headers.get_list("set-cookie"))

            content = resp.content or b""
            truncated = len(content) > max_body_bytes
            if truncated:
                content = content[:max_body_bytes]

            encoding = resp.encoding or "utf-8"
            try:
                html = content.decode(encoding, errors="replace")
            except (LookupError, TypeError):
                html = content.decode("utf-8", errors="replace")

            return {
                "url": url,
                "final_url": str(resp.url),
                "status": resp.status_code,
                "redirect_chain": redirect_chain,
                "headers": {k.lower(): v for k, v in resp.headers.items()},
                "set_cookie_headers": set_cookie_headers,
                "html": html,
                "body_size_bytes": len(content),
                "fetch_error": None,
            }
    except Exception as e:  # noqa: BLE001 — record any transport failure as data
        return {
            "url": url,
            "final_url": url,
            "status": None,
            "redirect_chain": redirect_chain,
            "headers": {},
            "set_cookie_headers": [],
            "html": "",
            "body_size_bytes": 0,
            "fetch_error": f"{type(e).__name__}: {e}",
        }


def _robots_url_for(url: str) -> str:
    s = urlsplit(url)
    scheme = s.scheme or "https"
    netloc = s.netloc or s.path
    return urlunsplit((scheme, netloc, "/robots.txt", "", ""))
