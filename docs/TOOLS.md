# Tool reference — `mcp_cfdi_mx`

This file is generated from the MCP server's tool registry by `scripts/gen_tool_reference.py`. Do not edit it by hand; run the script instead.

**Tools:** 1

## `mx__get_supported_scope`

Return the CFDI document types, complementos, and sealing modes this package supports.

Reflects Phase 1 scope locked in context-library/countries/mx.md
(workspace root repo): CFDI 4.0 Ingreso + Egreso + Complemento de Pagos
2.0, PAC-agnostic sealing. Model generation for these document types is
implemented (`mcp_cfdi_mx.models`); XSD validation, sealing, and TFD
verification tools are tracked as the next build phase in
roadmap-2026.md, not yet implemented.

Returns:
    A `ScopeInfo` describing current scope, for callers to check before
    assuming a document type or complemento is supported.

_No parameters._
