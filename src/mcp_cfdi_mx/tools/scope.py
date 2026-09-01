"""Package scope introspection tool."""

from __future__ import annotations

from typing import TypedDict


class ScopeInfo(TypedDict):
    version: str
    phase: int
    supported_document_types: list[str]
    supported_complementos: list[str]
    sealing_modes: list[str]
    out_of_scope: list[str]


def mx__get_supported_scope() -> ScopeInfo:
    """Return the CFDI document types, complementos, and sealing modes this package supports.

    Reflects Phase 1 scope locked in context-library/countries/mx.md
    (workspace root repo): CFDI 4.0 Ingreso + Egreso + Complemento de Pagos
    2.0, PAC-agnostic sealing. Model generation for these document types is
    implemented (`mcp_cfdi_mx.models`); XSD validation, sealing, and TFD
    verification tools are tracked as the next build phase in
    roadmap-2026.md, not yet implemented.

    Returns:
        A dict describing current scope, for callers to check before
        assuming a document type or complemento is supported.
    """
    return ScopeInfo(
        version="4.0",
        phase=1,
        supported_document_types=["I", "E", "P"],
        supported_complementos=["Pagos 2.0"],
        sealing_modes=["local", "pac"],
        out_of_scope=[
            "Carta Porte",
            "Complemento de Nómina",
            "Retenciones e información de pagos",
            "Comercio Exterior",
        ],
    )


__all__ = ["mx__get_supported_scope"]
