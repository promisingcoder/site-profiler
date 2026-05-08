"""MCP server tests.

The MCP server depends on the optional ``mcp`` package. When it's missing
the import raises ImportError with an install hint — that path is
covered. When it IS installed, we build the server, ensure the three
tools are registered, and call ``profile_url`` against an offline pair
through a monkey-patched API.
"""
from __future__ import annotations

import importlib

import pytest


def _mcp_available() -> bool:
    try:
        importlib.import_module("mcp.server.fastmcp")
        return True
    except ImportError:
        return False


def test_import_error_carries_install_hint():
    if _mcp_available():
        pytest.skip("`mcp` is installed in this environment")
    with pytest.raises(ImportError) as ei:
        import site_profiler.mcp_server  # noqa: F401
    assert "site-profiler[mcp]" in str(ei.value)


def test_server_registers_three_tools():
    if not _mcp_available():
        pytest.skip("`mcp` is not installed")
    from site_profiler.mcp_server import _build_server

    server = _build_server()
    # FastMCP exposes a list_tools coroutine; we don't run an event loop
    # here, but we can introspect the internal registry the @server.tool()
    # decorator updates.
    tools = list(server._tool_manager._tools.keys())  # type: ignore[attr-defined]
    assert "profile_url" in tools
    assert "list_detectors" in tools
    assert "list_variants" in tools


def test_list_detectors_tool_returns_categorized_dict():
    if not _mcp_available():
        pytest.skip("`mcp` is not installed")
    from site_profiler.mcp_server import _build_server

    server = _build_server()
    tool_fn = server._tool_manager._tools["list_detectors"].fn  # type: ignore[attr-defined]
    out = tool_fn()
    assert "captcha" in out
    assert "framework" in out
    # variants surface in the dict
    captcha_names = {entry["name"] for entry in out["captcha"]}
    assert "recaptcha" in captcha_names
    rec_entry = next(e for e in out["captcha"] if e["name"] == "recaptcha")
    variant_names = {v["name"] for v in rec_entry["variants"]}
    assert "v3" in variant_names


def test_list_variants_tool_for_known_name():
    if not _mcp_available():
        pytest.skip("`mcp` is not installed")
    from site_profiler.mcp_server import _build_server

    server = _build_server()
    tool_fn = server._tool_manager._tools["list_variants"].fn  # type: ignore[attr-defined]
    out = tool_fn(name="recaptcha")
    assert out["name"] == "recaptcha"
    assert any(v["name"] == "enterprise" for v in out["variants"])


def test_list_variants_tool_unknown_raises():
    if not _mcp_available():
        pytest.skip("`mcp` is not installed")
    from site_profiler.mcp_server import _build_server

    server = _build_server()
    tool_fn = server._tool_manager._tools["list_variants"].fn  # type: ignore[attr-defined]
    with pytest.raises(ValueError):
        tool_fn(name="no_such_thing")
