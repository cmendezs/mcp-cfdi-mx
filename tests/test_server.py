"""Smoke test for the MCP server entry point."""

from __future__ import annotations

from mcp_cfdi_mx.server import mcp


def test_server_imports_and_has_a_name() -> None:
    assert mcp is not None
