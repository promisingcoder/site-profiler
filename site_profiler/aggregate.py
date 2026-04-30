"""Run all detectors over a FetchedPair, compute block status + strategy, build SiteProfile."""
from __future__ import annotations

from datetime import datetime, timezone

from .block_status import compute_block_status
from .csp_hints import extract_csp_hints
from .parse import FetchedPair
from .registry import get_detectors, get_hydration_detectors
from .schema import (
    Evidence,
    HydrationBlob,
    RobotsInfo,
    SiteProfile,
    StructuredData,
    Transport,
)
from .strategy import rank_strategy


def aggregate(pair: FetchedPair) -> SiteProfile:
    # Trigger detector module imports lazily so registry is populated
    from . import detectors  # noqa: F401

    home = pair.home

    edge = _run("edge", pair)
    bot_protection = _run("bot_protection", pair)
    captcha = _run("captcha", pair)
    framework = _run("framework", pair)

    hydration_blobs: list[HydrationBlob] = []
    for fn in get_hydration_detectors():
        hydration_blobs.extend(fn(pair))
    # dedupe by name (keep first-seen, summing sizes if same)
    seen: dict[str, HydrationBlob] = {}
    for hb in hydration_blobs:
        if hb.name not in seen:
            seen[hb.name] = hb
        else:
            existing = seen[hb.name]
            existing.size_bytes = max(existing.size_bytes, hb.size_bytes)
    hydration_blobs = list(seen.values())

    structured = StructuredData(
        json_ld_present=bool(home.json_ld_blocks),
        json_ld_types=home.json_ld_types,
        opengraph=home.has_opengraph,
        twitter_cards=home.has_twitter_cards,
        microdata=home.has_microdata,
        microdata_types=home.microdata_types,
    )

    csp_hints = extract_csp_hints(home.csp)

    robots_info = RobotsInfo(
        status=pair.robots.status,
        bytes=pair.robots.body_size_bytes,
        sitemap_urls=pair.robots_parsed.sitemap_urls,
        crawl_delay=pair.robots_parsed.crawl_delay,
        has_disallow_all=pair.robots_parsed.has_disallow_all,
        comments=pair.robots_parsed.comments,
        nonstandard_directives=pair.robots_parsed.nonstandard_directives,
    )

    transport = Transport(
        status=home.status,
        redirect_chain=home.redirect_chain,
        final_url=home.final_url,
        body_size_bytes=home.body_size_bytes,
        fetch_error=home.fetch_error,
    )

    block_status, block_evidence = compute_block_status(pair)

    strategy = rank_strategy(
        block_status=block_status,
        framework=framework,
        hydration_blobs=hydration_blobs,
        structured=structured,
        body_size=home.body_size_bytes,
    )

    return SiteProfile(
        request_url=home.url,
        final_url=home.final_url,
        fetched_at=datetime.now(timezone.utc),
        transport=transport,
        edge=edge,
        bot_protection=bot_protection,
        captcha=captcha,
        framework=framework,
        hydration_blobs=hydration_blobs,
        structured_data=structured,
        csp_hints=csp_hints,
        robots=robots_info,
        block_status=block_status,
        block_evidence=block_evidence,
        strategy=strategy,
    )


def _run(category: str, pair: FetchedPair) -> list[Evidence]:
    out: list[Evidence] = []
    for fn in get_detectors(category):
        try:
            ev = fn(pair)
        except Exception as e:  # detector bugs shouldn't kill profiling
            ev = Evidence(
                name=f"_detector_error:{getattr(fn, '__name__', '?')}",
                detected=False,
                confidence=0.0,
                markers=[f"{type(e).__name__}: {e}"],
            )
        if ev is not None and ev.detected:
            out.append(ev)
    # Dedupe by name (keep highest confidence, merge markers)
    by_name: dict[str, Evidence] = {}
    for e in out:
        if e.name not in by_name:
            by_name[e.name] = e
        else:
            cur = by_name[e.name]
            if e.confidence > cur.confidence:
                cur.confidence = e.confidence
            for m in e.markers:
                if m not in cur.markers:
                    cur.markers.append(m)
    return list(by_name.values())
