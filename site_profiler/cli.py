"""CLI: python -m site_profiler <url>"""
from __future__ import annotations

import argparse
import sys

from .api import profile_url
from .fetch import CHROME_UA, DEFAULT_MAX_BODY, DEFAULT_TIMEOUT


def main(argv: list[str] | None = None) -> int:
    # Ensure UTF-8 stdout on Windows so JSON with any non-ASCII renders correctly.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    parser = argparse.ArgumentParser(
        prog="site-profiler",
        description="Profile a URL: tech stack, anti-bot, framework, robots, extraction strategy.",
    )
    parser.add_argument("url", help="URL to profile")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Per-request timeout in seconds")
    parser.add_argument("--max-body-bytes", type=int, default=DEFAULT_MAX_BODY, help="Max bytes to read from each response")
    parser.add_argument("--user-agent", default=CHROME_UA, help="User-Agent override")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent level")
    args = parser.parse_args(argv)

    profile = profile_url(
        args.url,
        timeout=args.timeout,
        max_body_bytes=args.max_body_bytes,
        user_agent=args.user_agent,
    )
    sys.stdout.write(profile.model_dump_json(indent=args.indent))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
