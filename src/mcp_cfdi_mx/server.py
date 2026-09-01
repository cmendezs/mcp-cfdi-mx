"""MCP server entry point — registers all Mexican e-invoicing tools."""

from typing import Any

from mcp_einvoicing_core import EInvoicingMCPServer

from mcp_cfdi_mx.tools.scope import mx__get_supported_scope


def _register_mx_tools(mcp: Any) -> None:
    """Register all Mexican e-invoicing tools onto the shared FastMCP instance."""
    mcp.tool()(mx__get_supported_scope)


mcp = EInvoicingMCPServer(
    "mcp-cfdi-mx",
    instructions=(
        "Tools for Mexican electronic invoicing: CFDI 4.0 (Ingreso, Egreso) and "
        "Complemento de Pagos 2.0, generated and validated against SAT's Anexo 20 "
        "standard. PAC-agnostic — supports both locally-sealed and PAC-sealed CFDI "
        "output. Phase 1 scope; see README for what is and is not yet implemented."
    ),
)
mcp.register_plugin(_register_mx_tools, "mx")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
