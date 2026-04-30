"""Pre-parse a fetched response into a FetchedPage / FetchedPair.

Detectors consume FetchedPair only — no detector re-tokenizes HTML.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from selectolax.parser import HTMLParser


# ----- raw helpers -----

def parse_set_cookies(set_cookie_headers: list[str]) -> tuple[list[str], dict[str, str]]:
    """Return (names_in_order_first_seen, name_to_value_dict)."""
    names: list[str] = []
    values: dict[str, str] = {}
    seen: set[str] = set()
    for header in set_cookie_headers:
        if not header:
            continue
        first = header.split(";", 1)[0]
        if "=" not in first:
            continue
        name, value = first.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name or name in seen:
            continue
        names.append(name)
        values[name] = value
        seen.add(name)
    return names, values


def parse_csp(value: str) -> dict[str, list[str]]:
    if not value:
        return {}
    out: dict[str, list[str]] = {}
    for clause in value.split(";"):
        clause = clause.strip()
        if not clause:
            continue
        parts = clause.split()
        if not parts:
            continue
        directive, *sources = parts
        out[directive.lower()] = sources
    return out


def parse_server_timing(value: str) -> list[tuple[str, dict[str, str]]]:
    if not value:
        return []
    out: list[tuple[str, dict[str, str]]] = []
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(";")
        name = parts[0].strip()
        params: dict[str, str] = {}
        for p in parts[1:]:
            p = p.strip()
            if "=" in p:
                k, v = p.split("=", 1)
                params[k.strip().lower()] = v.strip().strip('"')
            else:
                params[p.lower()] = ""
        out.append((name, params))
    return out


def parse_robots(text: str) -> dict:
    if not text:
        return {
            "sitemap_urls": [],
            "crawl_delay": None,
            "has_disallow_all": False,
            "comments": [],
            "nonstandard_directives": {},
        }
    sitemaps: list[str] = []
    crawl_delays: list[float] = []
    has_disallow_all = False
    comments: list[str] = []
    nonstandard: dict[str, list[str]] = {}
    current_uas: list[str] = []
    standard = {"user-agent", "disallow", "allow", "sitemap", "crawl-delay", "host"}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            c = line.lstrip("#").strip()
            if c:
                comments.append(c)
            continue
        if "#" in line:
            line, _ = line.split("#", 1)
            line = line.strip()
        if ":" not in line:
            continue
        directive, value = line.split(":", 1)
        directive = directive.strip().lower()
        value = value.strip()
        if directive == "user-agent":
            current_uas = [value.lower()]
        elif directive == "sitemap":
            if value:
                sitemaps.append(value)
        elif directive == "crawl-delay":
            try:
                crawl_delays.append(float(value))
            except ValueError:
                pass
        elif directive == "disallow":
            if value == "/" and ("*" in current_uas or "" in current_uas):
                has_disallow_all = True
        elif directive in standard:
            pass
        else:
            nonstandard.setdefault(directive, []).append(value)

    return {
        "sitemap_urls": sitemaps,
        "crawl_delay": min(crawl_delays) if crawl_delays else None,
        "has_disallow_all": has_disallow_all,
        "comments": comments[:50],
        "nonstandard_directives": nonstandard,
    }


def _extract_host(url: str) -> str | None:
    if not url:
        return None
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith(("http://", "https://")):
        try:
            return urlsplit(url).netloc.lower() or None
        except Exception:
            return None
    return None


def _flatten_json_ld_types(obj) -> list[str]:
    out: list[str] = []
    if isinstance(obj, dict):
        t = obj.get("@type")
        if isinstance(t, str):
            out.append(t)
        elif isinstance(t, list):
            for x in t:
                if isinstance(x, str):
                    out.append(x)
        for v in obj.values():
            out.extend(_flatten_json_ld_types(v))
    elif isinstance(obj, list):
        for item in obj:
            out.extend(_flatten_json_ld_types(item))
    return out


# ----- HTML body parser -----

def parse_body(html: str) -> dict:
    out = {
        "title": "",
        "html_class": "",
        "body_class": "",
        "html_attrs": {},
        "body_attrs": {},
        "metas": {},
        "meta_generators": [],
        "links": [],
        "script_srcs": [],
        "script_src_hosts": [],
        "inline_script_samples": [],
        "json_ld_blocks": [],
        "json_ld_types": [],
        "has_opengraph": False,
        "has_twitter_cards": False,
        "microdata_types": [],
        "has_microdata": False,
        "named_json_islands": [],  # (id, type, size, sample)
        "body_lower": "",
    }
    if not html:
        return out

    out["body_lower"] = html.lower()
    try:
        tree = HTMLParser(html)
    except Exception:
        return out
    if tree is None or tree.body is None and tree.head is None:
        # Not real HTML; skip parse but keep body_lower
        return out

    title = tree.css_first("title")
    out["title"] = (title.text() if title else "") or ""

    html_node = tree.css_first("html")
    if html_node is not None:
        out["html_attrs"] = dict(html_node.attributes or {})
        out["html_class"] = out["html_attrs"].get("class", "") or ""
    body_node = tree.css_first("body")
    if body_node is not None:
        out["body_attrs"] = dict(body_node.attributes or {})
        out["body_class"] = out["body_attrs"].get("class", "") or ""

    metas: dict[str, str] = {}
    meta_generators: list[str] = []
    has_og = False
    has_tw = False
    for m in tree.css("meta"):
        attrs = m.attributes or {}
        name = (attrs.get("name") or "").strip()
        prop = (attrs.get("property") or "").strip()
        content = (attrs.get("content") or "").strip()
        if name.lower() == "generator" and content:
            meta_generators.append(content)
        if name:
            metas[name.lower()] = content
        if prop:
            metas[prop.lower()] = content
        if prop.lower().startswith("og:"):
            has_og = True
        if name.lower().startswith("twitter:"):
            has_tw = True
    out["metas"] = metas
    out["meta_generators"] = meta_generators
    out["has_opengraph"] = has_og
    out["has_twitter_cards"] = has_tw

    links: list[dict[str, str]] = []
    for link in tree.css("link"):
        attrs = link.attributes or {}
        rel = attrs.get("rel") or ""
        href = attrs.get("href") or ""
        if rel and href:
            links.append({"rel": rel, "href": href, "type": attrs.get("type", "") or ""})
    out["links"] = links

    script_srcs: list[str] = []
    script_src_hosts: list[str] = []
    inline_samples: list[str] = []
    json_ld_blocks: list[dict] = []
    json_ld_types: list[str] = []
    named_islands: list[tuple[str, str, int, str]] = []

    for s in tree.css("script"):
        attrs = s.attributes or {}
        src = attrs.get("src")
        type_attr = (attrs.get("type") or "").lower()
        sid = attrs.get("id") or ""
        if src:
            script_srcs.append(src)
            host = _extract_host(src)
            if host:
                script_src_hosts.append(host)
            continue

        text = s.text() or ""
        if not text:
            continue
        text_len = len(text)

        if type_attr == "application/ld+json":
            try:
                data = json.loads(text)
            except Exception:
                continue

            def _try_block(item):
                if not isinstance(item, dict):
                    return
                ctx = item.get("@context", "")
                ctx_str = json.dumps(ctx) if not isinstance(ctx, str) else ctx
                if "schema.org" in ctx_str:
                    json_ld_blocks.append(item)
                    json_ld_types.extend(_flatten_json_ld_types(item))

            if isinstance(data, list):
                for item in data:
                    _try_block(item)
            else:
                _try_block(data)
        elif type_attr == "application/json" and sid:
            named_islands.append((sid, type_attr, text_len, text[:200]))
        elif sid == "__NEXT_DATA__":
            named_islands.append(("__NEXT_DATA__", type_attr or "application/json", text_len, text[:200]))
        else:
            inline_samples.append(text[:500])

    out["script_srcs"] = script_srcs
    out["script_src_hosts"] = list(dict.fromkeys(script_src_hosts))
    out["inline_script_samples"] = inline_samples[:50]
    out["json_ld_blocks"] = json_ld_blocks
    out["json_ld_types"] = list(dict.fromkeys(json_ld_types))
    out["named_json_islands"] = named_islands

    # microdata
    has_microdata = False
    microdata_types: list[str] = []
    for el in tree.css("[itemtype]"):
        has_microdata = True
        itemtype = (el.attributes or {}).get("itemtype", "") or ""
        if "schema.org" in itemtype:
            type_name = itemtype.rstrip("/").rsplit("/", 1)[-1]
            if type_name and type_name not in microdata_types:
                microdata_types.append(type_name)
    out["has_microdata"] = has_microdata
    out["microdata_types"] = microdata_types

    return out


# ----- dataclasses -----

@dataclass
class FetchedPage:
    url: str
    final_url: str
    status: int | None
    redirect_chain: list[tuple[int, str]]
    headers_lc: dict[str, str]
    set_cookie_names: list[str]
    set_cookie_values: dict[str, str]
    csp: dict[str, list[str]]
    server_timing: list[tuple[str, dict[str, str]]]
    html: str
    body_size_bytes: int
    fetch_error: str | None
    title: str
    html_class: str
    body_class: str
    html_attrs: dict[str, str]
    body_attrs: dict[str, str]
    metas: dict[str, str]
    meta_generators: list[str]
    links: list[dict[str, str]]
    script_srcs: list[str]
    script_src_hosts: list[str]
    inline_script_samples: list[str]
    json_ld_blocks: list[dict]
    json_ld_types: list[str]
    has_opengraph: bool
    has_twitter_cards: bool
    microdata_types: list[str]
    has_microdata: bool
    named_json_islands: list[tuple[str, str, int, str]]
    body_lower: str

    def header(self, name: str) -> str:
        return self.headers_lc.get(name.lower(), "") or ""


@dataclass
class RobotsParsed:
    sitemap_urls: list[str] = field(default_factory=list)
    crawl_delay: float | None = None
    has_disallow_all: bool = False
    comments: list[str] = field(default_factory=list)
    nonstandard_directives: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class FetchedPair:
    home: FetchedPage
    robots: FetchedPage
    robots_parsed: RobotsParsed


def build_page(data: dict) -> FetchedPage:
    headers_lc = data.get("headers", {})
    set_cookie_headers = data.get("set_cookie_headers", [])
    cookie_names, cookie_values = parse_set_cookies(set_cookie_headers)
    csp = parse_csp(headers_lc.get("content-security-policy", ""))
    server_timing = parse_server_timing(headers_lc.get("server-timing", ""))
    parsed = parse_body(data.get("html", "") or "")

    return FetchedPage(
        url=data.get("url", ""),
        final_url=data.get("final_url", "") or data.get("url", ""),
        status=data.get("status"),
        redirect_chain=data.get("redirect_chain", []),
        headers_lc=headers_lc,
        set_cookie_names=cookie_names,
        set_cookie_values=cookie_values,
        csp=csp,
        server_timing=server_timing,
        html=data.get("html", "") or "",
        body_size_bytes=data.get("body_size_bytes", 0),
        fetch_error=data.get("fetch_error"),
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


def build_pair(home_data: dict, robots_data: dict) -> FetchedPair:
    home = build_page(home_data)
    robots = build_page(robots_data)
    rp = parse_robots(robots.html)
    robots_parsed = RobotsParsed(
        sitemap_urls=rp["sitemap_urls"],
        crawl_delay=rp["crawl_delay"],
        has_disallow_all=rp["has_disallow_all"],
        comments=rp["comments"],
        nonstandard_directives=rp["nonstandard_directives"],
    )
    return FetchedPair(home=home, robots=robots, robots_parsed=robots_parsed)
