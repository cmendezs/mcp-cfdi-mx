"""Tests for mcp_cfdi_mx.tools.scope."""

from __future__ import annotations

from mcp_cfdi_mx.tools.scope import mx__get_supported_scope


def test_returns_phase_1_scope() -> None:
    scope = mx__get_supported_scope()
    assert scope.phase == 1
    assert set(scope.supported_document_types) == {"I", "E", "P"}
    assert "Pagos 2.0" in scope.supported_complementos
    assert set(scope.sealing_modes) == {"local", "pac"}


def test_out_of_scope_lists_deferred_complementos() -> None:
    scope = mx__get_supported_scope()
    assert "Carta Porte" in scope.out_of_scope
    assert "Complemento de Nómina" in scope.out_of_scope
