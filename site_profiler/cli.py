"""Command-line entry point.

Subcommands:
    profile <url>      Profile a URL → SiteProfile JSON (default if a URL is
                       passed without a subcommand).
    list-detectors     List all registered detectors, grouped by category.
                       Shows variants and their labels too.
    list-variants <name>
                       Show variants and their match logic for a specific
                       detector by name (e.g. ``recaptcha`` or ``next.js``).
    serve-mcp [--stdio]
                       Run as an MCP server. Requires the optional ``mcp``
                       dependency (``pip install site-profiler[mcp]``).

Backward compatibility: ``site-profiler https://example.com/`` (no
subcommand) still works — the URL form-positional is auto-detected and
routed to ``profile``.
"""
from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .api import profile_url
from .fetch import CHROME_UA, DEFAULT_MAX_BODY, DEFAULT_TIMEOUT


# ---------------------------------------------------------------------------
# Subcommand: profile
# ---------------------------------------------------------------------------


def _add_profile_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("url", help="URL to profile")
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                   help="Per-request timeout in seconds")
    p.add_argument("--max-body-bytes", type=int, default=DEFAULT_MAX_BODY,
                   help="Max bytes to read from each response")
    p.add_argument("--user-agent", default=CHROME_UA, help="User-Agent override")
    p.add_argument("--indent", type=int, default=2, help="JSON indent level")


def _cmd_profile(args: argparse.Namespace) -> int:
    profile = profile_url(
        args.url,
        timeout=args.timeout,
        max_body_bytes=args.max_body_bytes,
        user_agent=args.user_agent,
    )
    sys.stdout.write(profile.model_dump_json(indent=args.indent))
    sys.stdout.write("\n")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: list-detectors
# ---------------------------------------------------------------------------


def _cmd_list_detectors(args: argparse.Namespace) -> int:
    # Trigger registration
    from . import detectors  # noqa: F401
    from .registry import all_categories, get_detectors
    from .detectors.base import Detector

    # Build a lookup from registered runner __name__ → owning Detector class.
    cls_by_name: dict[str, type[Detector]] = {}
    for sub in _all_detector_subclasses(Detector):
        if not sub.__dict__.get("abstract", False) and sub.name:
            cls_by_name[sub.name] = sub

    for cat in sorted(all_categories()):
        print(f"[{cat}]")
        for fn in get_detectors(cat):
            cls = cls_by_name.get(fn.__name__)
            if cls is not None and cls.variants:
                vs = ", ".join(v.name for v in cls.variants)
                print(f"  {fn.__name__:<20s}  variants: {vs}")
            else:
                print(f"  {fn.__name__}")
        print()
    return 0


def _all_detector_subclasses(root: type) -> list[type]:
    out: list[type] = []
    stack = [root]
    while stack:
        c = stack.pop()
        for sub in c.__subclasses__():
            out.append(sub)
            stack.append(sub)
    return out


# ---------------------------------------------------------------------------
# Subcommand: list-variants
# ---------------------------------------------------------------------------


def _cmd_list_variants(args: argparse.Namespace) -> int:
    from . import detectors  # noqa: F401
    from .detectors.base import Detector

    target_name = args.name
    for sub in _all_detector_subclasses(Detector):
        if sub.__dict__.get("abstract", False):
            continue
        if sub.name != target_name:
            continue
        print(f"{sub.name}  ({sub.__module__})")
        if not sub.variants:
            print("  (no variants declared)")
            return 0
        for v in sub.variants:
            print(f"  - {v.name:<20s}  {v.label or ''}")
        return 0

    print(f"detector {target_name!r} not found", file=sys.stderr)
    print("hint: run `site-profiler list-detectors` to see all names", file=sys.stderr)
    return 2


# ---------------------------------------------------------------------------
# Subcommand: serve-mcp
# ---------------------------------------------------------------------------


def _cmd_serve_mcp(args: argparse.Namespace) -> int:
    try:
        from .mcp_server import run as run_mcp
    except ImportError as e:
        print(
            f"MCP server unavailable: {e}\n"
            "Install with: pip install site-profiler[mcp]",
            file=sys.stderr,
        )
        return 2
    run_mcp()
    return 0


# ---------------------------------------------------------------------------
# Top-level dispatch
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="site-profiler",
        description="Profile a URL: tech stack, anti-bot, framework, robots, extraction strategy.",
    )
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("profile", help="Profile a URL (default action)")
    _add_profile_args(sp)
    sp.set_defaults(func=_cmd_profile)

    sp = sub.add_parser("list-detectors", help="List all registered detectors")
    sp.set_defaults(func=_cmd_list_detectors)

    sp = sub.add_parser("list-variants", help="List variants of a specific detector")
    sp.add_argument("name", help="Detector name (e.g. recaptcha, next.js)")
    sp.set_defaults(func=_cmd_list_variants)

    sp = sub.add_parser("serve-mcp", help="Run as an MCP server (stdio transport)")
    sp.set_defaults(func=_cmd_serve_mcp)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    # Ensure UTF-8 stdout on Windows so JSON with any non-ASCII renders correctly.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

    if argv is None:
        argv = sys.argv[1:]

    # Backward compat: a single URL-like positional with no subcommand → profile
    KNOWN_CMDS = {"profile", "list-detectors", "list-variants", "serve-mcp", "-h", "--help"}
    if argv and argv[0] not in KNOWN_CMDS and not argv[0].startswith("--"):
        # treat as legacy `site-profiler <url> [opts...]`
        argv = ["profile", *argv]

    parser = _build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
