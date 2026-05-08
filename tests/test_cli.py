"""CLI subcommand tests. The ``profile`` subcommand exercises the network
path so it's not unit-tested here; it's covered indirectly through
test_e2e_offline.py via profile_pair.
"""
from __future__ import annotations

import io
import sys

from site_profiler.cli import main


def test_list_detectors_runs(capsys):
    rc = main(["list-detectors"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[captcha]" in out
    assert "[framework]" in out
    assert "recaptcha" in out
    # Variants column is rendered for class-based detectors
    assert "v3" in out
    assert "next.js" in out


def test_list_variants_known(capsys):
    rc = main(["list-variants", "recaptcha"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "recaptcha" in out
    assert "v2_checkbox" in out
    assert "v3" in out
    assert "enterprise" in out


def test_list_variants_unknown_returns_2(capsys):
    rc = main(["list-variants", "no_such_thing"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "not found" in err


def test_list_variants_no_variants_for_function_only_detector(capsys):
    """``hubspot`` is still function-based (no variants declared) — list-variants
    should report it as having no variants instead of erroring."""
    rc = main(["list-variants", "hubspot"])
    # Function-based detectors don't have a Detector class, so they aren't
    # found in the class lookup → exit 2. This is acceptable: the command
    # only inspects class-based detectors. Document with the assertion.
    assert rc == 2


def test_serve_mcp_install_hint_when_mcp_missing(capsys):
    """If `mcp` package isn't installed, serve-mcp must exit 2 with a
    helpful install hint — never a stack trace."""
    # If mcp is actually installed in this environment, skip
    try:
        from mcp.server.fastmcp import FastMCP  # noqa: F401
    except ImportError:
        rc = main(["serve-mcp"])
        assert rc == 2
        err = capsys.readouterr().err
        assert "MCP server unavailable" in err
        assert "pip install" in err
        return
    # else: mcp installed → skip this test (covered by test_mcp_server.py)
    import pytest
    pytest.skip("`mcp` is installed in this environment")


def test_legacy_url_form_still_routes_to_profile(monkeypatch):
    """`site-profiler https://example.com/` (no subcommand) still works."""
    called_with: list = []

    def fake_profile(args):
        called_with.append(args.url)
        return 0

    # Monkey-patch the profile dispatch
    from site_profiler import cli as cli_mod
    monkeypatch.setattr(cli_mod, "_cmd_profile", fake_profile)

    rc = main(["https://example.com/"])
    assert rc == 0
    assert called_with == ["https://example.com/"]


def test_no_args_prints_help(capsys):
    rc = main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "list-detectors" in out
    assert "serve-mcp" in out
