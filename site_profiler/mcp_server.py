"""Optional MCP (Model Context Protocol) server for site-profiler.

Exposes the profiler as MCP tools so it can be called from any MCP client
(Claude Desktop, Cline, the Anthropic SDK, custom hosts).

Tools exposed:
    - ``profile_url(url, timeout?, user_agent?)`` → JSON SiteProfile
    - ``list_detectors()`` → grouped detector + variant list
    - ``list_variants(name)`` → variants for a single detector

This module imports ``mcp`` lazily so that ``import site_profiler`` does
not require the optional dependency. The ``serve-mcp`` CLI subcommand is
the only entry that imports this module.

To run as a server::

    pip install site-profiler[mcp]
    site-profiler serve-mcp

Or, equivalently::

    python -m site_profiler serve-mcp

Then point your MCP client at the stdio transport.
"""
from __future__ import annotations

# This import is intentional and at module top-level — the CLI catches the
# ImportError and prints a helpful install hint. We don't want a confusing
# "site_profiler.mcp_server has no attribute X" instead.
try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    raise ImportError(
        "site_profiler.mcp_server requires the optional `mcp` package. "
        "Install with: pip install site-profiler[mcp]"
    ) from e

from .api import profile_url as _profile_url
from .fetch import CHROME_UA, DEFAULT_MAX_BODY, DEFAULT_TIMEOUT


_server: FastMCP | None = None


def _build_server() -> FastMCP:
    global _server
    if _server is not None:
        return _server

    server = FastMCP(name="site-profiler")

    @server.tool()
    def profile_url(
        url: str,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = CHROME_UA,
        max_body_bytes: int = DEFAULT_MAX_BODY,
    ) -> dict:
        """Profile a URL.

        Returns a JSON-serializable dict matching the ``SiteProfile`` schema:
        transport, edge, bot_protection, captcha, framework, hydration_blobs,
        structured_data, csp_hints, robots, block_status, strategy.

        Each detection carries ``(name, confidence, markers[], extra{},
        version?, variants[])``. Variant lists are populated for technologies
        with multiple sub-forms (reCAPTCHA v2/v3/Enterprise, Next.js Pages
        Router/App Router, Shopify core/Hydrogen, GeeTest v3/v4, etc.).
        """
        profile = _profile_url(
            url,
            timeout=timeout,
            max_body_bytes=max_body_bytes,
            user_agent=user_agent,
        )
        return profile.model_dump(mode="json")

    @server.tool()
    def list_detectors() -> dict:
        """List all registered detectors, grouped by category.

        Returns ``{"<category>": [{"name", "variants": [{"name", "label"}, ...]}, ...]}``.
        """
        from . import detectors  # noqa: F401  triggers registration
        from .registry import all_categories, get_detectors
        from .detectors.base import Detector

        cls_by_name: dict[str, type[Detector]] = {}
        for sub in _all_detector_subclasses(Detector):
            if not sub.__dict__.get("abstract", False) and sub.name:
                cls_by_name[sub.name] = sub

        out: dict[str, list[dict]] = {}
        for cat in sorted(all_categories()):
            entries: list[dict] = []
            for fn in get_detectors(cat):
                cls = cls_by_name.get(fn.__name__)
                variants = []
                if cls is not None:
                    for v in cls.variants:
                        variants.append({"name": v.name, "label": v.label})
                entries.append({"name": fn.__name__, "variants": variants})
            out[cat] = entries
        return out

    @server.tool()
    def list_variants(name: str) -> dict:
        """List variants for a specific detector by name.

        Returns ``{"name", "module", "variants": [{"name", "label"}, ...]}``
        or raises if the detector is not registered.
        """
        from . import detectors  # noqa: F401
        from .detectors.base import Detector

        for sub in _all_detector_subclasses(Detector):
            if sub.__dict__.get("abstract", False):
                continue
            if sub.name == name:
                return {
                    "name": sub.name,
                    "module": sub.__module__,
                    "variants": [
                        {"name": v.name, "label": v.label} for v in sub.variants
                    ],
                }
        raise ValueError(f"detector {name!r} not found")

    _server = server
    return server


def _all_detector_subclasses(root: type) -> list[type]:
    out: list[type] = []
    stack = [root]
    while stack:
        c = stack.pop()
        for sub in c.__subclasses__():
            out.append(sub)
            stack.append(sub)
    return out


def run() -> None:
    """Run the MCP server over stdio. Blocks until the client disconnects."""
    server = _build_server()
    server.run()
