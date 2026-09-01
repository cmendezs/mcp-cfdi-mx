# mcp-cfdi-mx 🇲🇽

[English](README.md) | [Español](README.es-MX.md)

<!-- mcp-name: io.github.cmendezs/mcp-cfdi-mx -->

![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
[![PyPI version](https://img.shields.io/pypi/v/mcp-cfdi-mx.svg)](https://pypi.org/project/mcp-cfdi-mx/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-cfdi-mx.svg)](https://pypi.org/project/mcp-cfdi-mx/)

A Python MCP server providing tools for Mexican **electronic invoicing** compliant with **CFDI 4.0** and **Complemento de Pagos 2.0**, per SAT's Anexo 20 technical standard. It enables AI agents (Claude, IDEs) to build, XSD-validate, and seal CFDI 4.0 documents (Ingreso, Egreso, and Complemento de Pagos 2.0), verify a PAC-returned Timbre Fiscal Digital stamp, and validate Mexican RFC tax identifiers.

**Phase 1 scope.** This package covers CFDI 4.0 Ingreso, Egreso, and Complemento de Pagos 2.0 only — Carta Porte, Complemento de Nómina, Retenciones, and Comercio Exterior are not yet supported, and it does not submit to any PAC. See [Available tools](#available-tools) for exactly what is implemented today.

---

## Introduction

This package is built on [**mcp-einvoicing-core**](https://github.com/cmendezs/mcp-einvoicing-core), the shared base library for e-invoicing MCP servers. It provides the `InvoiceDocument` model base, the `TaxIdentifier.validate_mx_rfc` RFC validator, and `SelloDigitalSigner` — the MX-specific concrete implementation of core's document-signing abstraction (SHA-256 digest of the cadena original, RSA-PKCS#1v1.5-signed with the emisor's CSD, per SAT's Anexo 20).

`mcp-einvoicing-core` is installed automatically as a dependency, no additional step is required.

CFDI is a **clearance-model** standard: a CFDI becomes legally valid only once a PAC (Proveedor Autorizado de Certificación) certifies it and returns a Timbre Fiscal Digital (TFD). This package does not submit to a PAC — it is **PAC-agnostic**, producing either a locally-sealed CFDI (ready to hand to any PAC that accepts pre-sealed documents) or an unsealed, schema-valid CFDI (for a PAC that seals on the emisor's behalf), selected via a `sealing_mode` parameter.

## Installation

### Via PyPI (recommended)

```bash
pip install mcp-cfdi-mx
```

Or without prior installation using `uvx`:

```bash
uvx mcp-cfdi-mx
```

### From source

```bash
git clone https://github.com/cmendezs/mcp-cfdi-mx.git
cd mcp-cfdi-mx
uv sync --all-extras
```

## Configuration (environment variables)

This package has no required environment variables. CSD certificate/key paths and passwords
are passed as tool arguments (file paths or environment references — never plaintext key
material embedded in a request), not read from a fixed environment variable name.

## Claude Desktop integration

Add the following configuration to your `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "cfdi-mx": {
      "command": "uvx",
      "args": ["mcp-cfdi-mx"]
    }
  }
}
```

## Cursor integration

Cursor supports MCP servers via stdio. Add the configuration to:
- **Globally** (all projects): `~/.cursor/mcp.json`
- **Per project** (this repository only): `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "cfdi-mx": {
      "command": "uvx",
      "args": ["mcp-cfdi-mx"]
    }
  }
}
```

Reload the Cursor window (`Ctrl+Shift+P` → *Reload Window*) after saving changes.

## Kiro integration

Kiro supports MCP servers through a dedicated configuration file:
- **Globally**: `~/.kiro/settings/mcp.json`
- **Workspace**: `.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "cfdi-mx": {
      "command": "uvx",
      "args": ["mcp-cfdi-mx"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

> **Security tip**: if a future tool version accepts credentials via environment reference,
> use the syntax `"VAR_NAME": "${VAR_NAME}"` so Kiro resolves it from the shell rather than
> storing it in plaintext.

## Available tools

### Build

| Tool | Description |
|------|-------------|
| `mx__build_cfdi` | Build a well-formed, unsealed CFDI 4.0 `Comprobante` XML (Ingreso or Egreso) from structured input |
| `mx__build_pago` | Build a Complemento de Pagos 2.0 CFDI (`TipoDeComprobante="P"`), composing the fixed single-`Concepto` wrapper SAT's guide mandates |

### Validate and seal

| Tool | Description |
|------|-------------|
| `mx__validate_cfdi` | Full XSD validation against `cfdv40.xsd`, plus `TimbreFiscalDigitalv11.xsd.xml` and/or `Pagos20.xsd.xml` when those complements are present |
| `mx__seal_cfdi` | Compute the Sello Digital via `SelloDigitalSigner`, `sealing_mode`-aware (`"local"` \| `"pac"`) |
| `mx__verify_tfd` | Parse a PAC-returned Timbre Fiscal Digital 1.1 stamp, and cryptographically verify `SelloSAT` when the PAC's certificate is supplied |

### Scope

| Tool | Description |
|------|-------------|
| `mx__get_supported_scope` | Returns the CFDI document types, complementos, and sealing modes this package currently supports |

See [`docs/TOOLS.md`](docs/TOOLS.md) for the full parameter reference of every tool, generated from the live tool registry.

### Not yet implemented

PAC submission transport (this package is PAC-agnostic and does not submit to any specific PAC), and later-phase complementos (Carta Porte, Complemento de Nómina, Retenciones, Comercio Exterior) — tracked in `context-library/roadmap-2026.md` (workspace root repo).

## Architecture

`mcp_cfdi_mx.models.CFDIComprobante` extends `mcp_einvoicing_core.models.InvoiceDocument` (the
non-EN 16931 pathway — CFDI predates and has no lineage to CEN TC 434, the same determination
as `mcp-nfe-br`). RFC validation for both Emisor and Receptor routes through
`TaxIdentifier.validate_mx_rfc` (core). Sealing routes through
`mcp_einvoicing_core.digital_signature.SelloDigitalSigner`, the MX-specific concrete
implementation of core's `BaseDocumentSigner` — the same pattern ES (XAdES), BR (XML-DSig),
and IT (CAdES) use for their own signature standards.

```text
[ ERP System / Application ] <--> [ MCP Server ] <--> [ PAC (any, PAC-agnostic) / SAT ]
          ^                           |
          |                           v
   [ AI Agent (Claude) ] <--- (CFDI 4.0 / Pagos 2.0)
```

## Supported standards

| Standard | Version | Source |
|---|---|---|
| CFDI (Comprobante Fiscal Digital por Internet) | 4.0 | SAT Anexo 20, DOF 2022-01-13 |
| Timbre Fiscal Digital | 1.1 | SAT |
| Complemento de Pagos | 2.0 | SAT |

See [`specs/README.md`](specs/README.md) for the full source bundle and retrieval dates, and
[`context-library/countries/mx.md`](https://github.com/cmendezs/mcp-einvoicing/blob/main/context-library/countries/mx.md)
in the workspace root repo for the verified compliance reference.

## Tests

```bash
uv run pytest tests/ -v
```

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Other e-invoicing MCP servers

| Country | Server |
|---------|--------|
| 🌍 Global | [mcp-einvoicing-core](https://github.com/cmendezs/mcp-einvoicing-core) |
| 🇦🇪 United Arab Emirates | [mcp-einvoicing-ae](https://github.com/cmendezs/mcp-einvoicing-ae) |
| 🇧🇪 Belgium | [mcp-einvoicing-be](https://github.com/cmendezs/mcp-einvoicing-be) |
| 🇧🇷 Brazil | [mcp-nfe-br](https://github.com/cmendezs/mcp-nfe-br) |
| 🇫🇷 France | [mcp-facture-electronique-fr](https://github.com/cmendezs/mcp-facture-electronique-fr) |
| 🇩🇪 Germany | [mcp-einvoicing-de](https://github.com/cmendezs/mcp-einvoicing-de) |
| 🇮🇹 Italy | [mcp-fattura-elettronica-it](https://github.com/cmendezs/mcp-fattura-elettronica-it) |
| 🇵🇱 Poland | [mcp-ksef-pl](https://github.com/cmendezs/mcp-ksef-pl) |
| 🇸🇬 Singapore | [mcp-invoicenow-sg](https://github.com/cmendezs/mcp-invoicenow-sg) |
| 🇪🇸 Spain | [mcp-facturacion-electronica-es](https://github.com/cmendezs/mcp-facturacion-electronica-es) |

## License

This project is distributed under the **Apache 2.0** license.
See the [LICENSE](LICENSE) file for details. For the full version history, see [CHANGELOG.md](CHANGELOG.md).
