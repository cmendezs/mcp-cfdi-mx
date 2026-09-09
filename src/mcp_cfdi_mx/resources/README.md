# mcp-cfdi-mx — Runtime resources (shipped in the wheel)

XSD schemas and cadena original XSLT transforms this package loads at import
time. Moved here from the repo-root `specs/` directory 2026-09-09 (CORE-1,
`audit/2026-09-audit-core.md`): the previous location resolved a path outside
the installed package once pip-installed from a wheel, since only
`src/mcp_cfdi_mx/` is packaged (`[tool.hatch.build.targets.wheel]` in
`pyproject.toml`). `specs/` (repo root) still holds the reference-only
material (Anexo 20 PDFs, fill-in guides, catalogue workbooks) that nothing in
`src/` reads at runtime — see [`../../../specs/README.md`](../../../specs/README.md).

Provenance (authority URL, retrieval date) for every file below is recorded
in `specs/README.md`'s "Sources and versions" table, not duplicated here.

| File | Loaded by | Note |
|---|---|---|
| `cfdv40.xsd.xml` | `utils/xsd_validator.py` | CFDI 4.0 root schema |
| `tdCFDI.xsd` | `utils/xsd_validator.py` | Shared simple types (`xs:import`ed by `cfdv40.xsd.xml`) |
| `catCFDI.xsd` | `utils/xsd_validator.py` | Catalogue enumerations (`xs:import`ed by `cfdv40.xsd.xml`) |
| `TimbreFiscalDigitalv11.xsd.xml` | `utils/xsd_validator.py` | TFD 1.1 schema |
| `Pagos20.xsd.xml` | `utils/xsd_validator.py` | Complemento de Pagos 2.0 schema |
| `catPagos.xsd.xml` | `utils/xsd_validator.py` | Pagos 2.0 catalogue enumerations (`xs:import`ed by `Pagos20.xsd.xml`) |
| `cadenaoriginal_4_0.xslt` | `tools/seal.py` | Cadena original transform for the CFDI `Sello` |
| `utilerias.xslt` | `tools/seal.py` | Base helper templates, `xsl:include`d by `cadenaoriginal_4_0.xslt` |
| `Pagos20.xslt` | `tools/seal.py` | Pagos 2.0 cadena original fragment, `xsl:include`d by `cadenaoriginal_4_0.xslt` |
| `cadenaoriginal_TFD_1_1.xslt` | `utils/tfd.py` | TFD cadena original transform |

## Update process

When SAT publishes a new schema or transform version, replace the file here
directly (not in `specs/`) and update `specs/README.md`'s version/retrieval
columns to match.
