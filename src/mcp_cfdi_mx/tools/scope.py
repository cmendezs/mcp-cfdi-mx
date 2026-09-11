"""Package scope introspection tool."""

from __future__ import annotations

from mcp_einvoicing_core.base_server import BaseScopeInfo


class ScopeInfo(BaseScopeInfo):
    """MX's own scope fields on top of the shared base (core v1.32.0, CORE-8).

    Adds `supported_complementos` (Complemento de Pagos, Comercio Exterior,
    etc.) and `sealing_modes` (`local`/`pac`) — CFDI-specific dimensions the
    shared base does not know about. `version` is renamed `schema_version`
    to match the base field name.
    """

    supported_complementos: list[str]
    sealing_modes: list[str]


def mx__get_supported_scope() -> ScopeInfo:
    """Return the CFDI document types, complementos, and sealing modes this package supports.

    Reflects Phase 1 scope: CFDI 4.0 Ingreso + Egreso + Complemento de Pagos
    2.0, PAC-agnostic sealing. Build (`mx__build_cfdi`/`mx__build_pago`),
    XSD validation (`mx__validate_cfdi`), sealing (`mx__seal_cfdi`), and TFD
    verification (`mx__verify_tfd`) are all implemented. PAC submission
    transport and later-phase complementos are not.

    Returns:
        A `ScopeInfo` describing current scope, for callers to check before
        assuming a document type or complemento is supported.
    """
    return ScopeInfo(
        schema_version="4.0",
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


__all__ = ["mx__get_supported_scope", "ScopeInfo"]
