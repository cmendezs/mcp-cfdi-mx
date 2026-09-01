"""MCP server entry point — registers all Mexican e-invoicing tools."""

from typing import Any

from mcp_einvoicing_core import EInvoicingMCPServer

from mcp_cfdi_mx.tools.build import mx__build_cfdi
from mcp_cfdi_mx.tools.build_pago import mx__build_pago
from mcp_cfdi_mx.tools.scope import mx__get_supported_scope
from mcp_cfdi_mx.tools.seal import mx__seal_cfdi
from mcp_cfdi_mx.tools.validate import mx__validate_cfdi
from mcp_cfdi_mx.tools.verify_tfd import mx__verify_tfd


def _register_mx_tools(mcp: Any) -> None:
    """Register all Mexican e-invoicing tools onto the shared FastMCP instance."""
    mcp.tool()(mx__get_supported_scope)
    mcp.tool()(mx__build_cfdi)
    mcp.tool()(mx__build_pago)
    mcp.tool()(mx__validate_cfdi)
    mcp.tool()(mx__seal_cfdi)
    mcp.tool()(mx__verify_tfd)


mcp = EInvoicingMCPServer(
    "mcp-cfdi-mx",
    instructions=(
        "Tools for Mexican electronic invoicing: build, XSD-validate, and seal CFDI 4.0 "
        "(Ingreso, Egreso) and Complemento de Pagos 2.0 documents against SAT's Anexo 20 "
        "standard, and verify a PAC-returned Timbre Fiscal Digital 1.1 stamp. "
        "PAC-agnostic — mx__seal_cfdi supports both locally-sealed and PAC-sealed CFDI "
        "output via sealing_mode. Phase 1 scope (Ingreso/Egreso/Pagos 2.0 only); no PAC "
        "submission transport. See README for the full tool list and scope."
    ),
)
mcp.register_plugin(_register_mx_tools, "mx")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
