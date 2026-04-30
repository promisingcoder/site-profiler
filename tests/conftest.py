"""Test helpers: build synthetic FetchedPage / FetchedPair without network."""
from __future__ import annotations

from site_profiler.parse import (
    FetchedPage,
    FetchedPair,
    RobotsParsed,
    parse_body,
    parse_csp,
    parse_robots,
    parse_server_timing,
    parse_set_cookies,
)


def make_page(
    *,
    url: str = "https://example.com/",
    final_url: str | None = None,
    status: int | None = 200,
    html: str = "",
    headers: dict[str, str] | None = None,
    set_cookies: list[str] | None = None,
    body_size: int | None = None,
    fetch_error: str | None = None,
) -> FetchedPage:
    headers = headers or {}
    headers_lc = {k.lower(): v for k, v in headers.items()}
    set_cookie_headers = set_cookies or []
    cookie_names, cookie_values = parse_set_cookies(set_cookie_headers)
    csp = parse_csp(headers_lc.get("content-security-policy", ""))
    st = parse_server_timing(headers_lc.get("server-timing", ""))
    parsed = parse_body(html or "")
    final = final_url or url
    return FetchedPage(
        url=url,
        final_url=final,
        status=status,
        redirect_chain=[(status or 0, final)] if status is not None else [],
        headers_lc=headers_lc,
        set_cookie_names=cookie_names,
        set_cookie_values=cookie_values,
        csp=csp,
        server_timing=st,
        html=html,
        body_size_bytes=body_size if body_size is not None else len((html or "").encode("utf-8")),
        fetch_error=fetch_error,
        title=parsed["title"],
        html_class=parsed["html_class"],
        body_class=parsed["body_class"],
        html_attrs=parsed["html_attrs"],
        body_attrs=parsed["body_attrs"],
        metas=parsed["metas"],
        meta_generators=parsed["meta_generators"],
        links=parsed["links"],
        script_srcs=parsed["script_srcs"],
        script_src_hosts=parsed["script_src_hosts"],
        inline_script_samples=parsed["inline_script_samples"],
        json_ld_blocks=parsed["json_ld_blocks"],
        json_ld_types=parsed["json_ld_types"],
        has_opengraph=parsed["has_opengraph"],
        has_twitter_cards=parsed["has_twitter_cards"],
        microdata_types=parsed["microdata_types"],
        has_microdata=parsed["has_microdata"],
        named_json_islands=parsed["named_json_islands"],
        body_lower=parsed["body_lower"],
    )


def make_pair(
    home_kwargs: dict | None = None,
    robots_kwargs: dict | None = None,
) -> FetchedPair:
    home = make_page(**(home_kwargs or {}))
    if robots_kwargs is None:
        robots_kwargs = {"url": home.url + "robots.txt", "html": "", "status": 200}
    robots = make_page(**robots_kwargs)
    rp = parse_robots(robots.html)
    robots_parsed = RobotsParsed(
        sitemap_urls=rp["sitemap_urls"],
        crawl_delay=rp["crawl_delay"],
        has_disallow_all=rp["has_disallow_all"],
        comments=rp["comments"],
        nonstandard_directives=rp["nonstandard_directives"],
    )
    return FetchedPair(home=home, robots=robots, robots_parsed=robots_parsed)
