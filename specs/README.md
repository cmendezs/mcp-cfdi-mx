# mcp-cfdi-mx — Specification assets

This directory holds the normative source material for Mexico's CFDI 4.0, Timbre Fiscal
Digital 1.1, and Complemento de Pagos 2.0 — official schemas (XSD), cadena original
transforms (XSLT), the Anexo 20 technical standard and fill-in guides, and SAT's catalogue
workbooks. Values derived from these documents belong in
[`context-library/countries/mx.md`](../../context-library/countries/mx.md) (in the workspace
root repo), not in code and not duplicated as a new file in this directory.

## Directory layout

All files are kept flat at the top level of `specs/` — the package covers a single family
of related standards (CFDI 4.0 and its complementos), so no per-standard subdirectory split
is needed (contrast ES's `facturae/`/`sii/`/`verifactu/` split for genuinely distinct
systems).

## Sources and versions

| Standard | Version | Authority URL | Retrieved |
|---|---|---|---|
| Anexo 20 de la RMF (CFDI 4.0 technical standard) | 2022 (DOF 2022-01-13) | `http://omawww.sat.gob.mx/tramitesyservicios/Paginas/anexo_20.htm` (user-supplied; not independently fetched) | 2026-09-01 |
| CFDI 4.0 XSD (`cfdv40.xsd`) | 4.0 | `http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd` (user-supplied; not independently fetched) | 2026-09-01 |
| Timbre Fiscal Digital XSD | 1.1 | `[NEED: SAT TFD 1.1 canonical URL]` | 2026-09-01 |
| Complemento de Pagos 2.0 | 2.0 | `https://www.sat.gob.mx/portal/public/tramites/complemento-recepcion-de-pagos` (user-supplied; not independently fetched) | 2026-09-01 |
| Catálogos del CFDI (`catCFDI` workbook) | dated `20260821` | `[NEED: SAT catálogos page URL]` | 2026-09-01 |
| Matriz de errores CFDI 4.0 | dated `20260325` | `[NEED: SAT matriz de errores page URL]` | 2026-09-01 |

At least one row per standard listed in `pyproject.toml` is mandatory, each backed by an
official authority URL and an actual retrieval date. The three `[NEED:]` rows above have a
supplied local file but no independently-verified canonical URL; do not populate them from
memory — see `context-library/regulatory-watch/sources.md` for how these are tracked as
`manual` watch entries until a URL is confirmed.

## Files

| File | Role | Namespace / note |
|---|---|---|
| `cfdv40.xsd.xml` | CFDI 4.0 root schema | `http://www.sat.gob.mx/cfd/4` |
| `tdCFDI.xsd` | Shared simple types (RFC, importes, fechas) | `http://www.sat.gob.mx/sitio_internet/cfd/tipoDatos/tdCFDI` — normative RFC regex (`t_RFC`) lives here |
| `catCFDI.xsd` | Catalogue enumerations (schema-level) | `http://www.sat.gob.mx/sitio_internet/cfd/catalogos` |
| `catCFDI_V_4_20260821.xls` | Catalogue values workbook (all sheets, incl. `c_TasaOCuota` IVA/IEPS/ISR rates) | Code-list and rate source; parse with `xlrd` (legacy `.xls` binary format) |
| `cadenaoriginal_4_0.xslt` | Cadena original transform for the CFDI `Sello` | Hard dependency for sealing. Declares `xsl:include` of ~35 SAT-hosted complemento fragments by absolute URL — only `utilerias.xslt` (base helper templates, load-bearing for every field) and `Pagos20.xslt` (Phase-1 Pagos 2.0 fragment) are supplied; all others are safely stubbed at compile time by `SelloDigitalSigner`'s resolver since Phase 1 never emits those complementos. |
| `utilerias.xslt` | Base cadena original helper templates (`Requerido`/`Opcional`/`ManejaEspacios`) | Required by every attribute in `cadenaoriginal_4_0.xslt`; not a complemento-specific fragment |
| `Pagos20.xslt` | Cadena original fragment for the Complemento de Pagos 2.0 | Required for Phase-1 Pagos CFDIs |
| `TimbreFiscalDigitalv11.xsd.xml` | TFD 1.1 (PAC stamp) schema | `http://www.sat.gob.mx/TimbreFiscalDigital` |
| `cadenaoriginal_TFD_1_1.xslt` | TFD cadena original transform | For verifying the PAC's stamp |
| `Pagos20.xsd.xml` | Complemento de Pagos 2.0 schema | `http://www.sat.gob.mx/Pagos20` |
| `catPagos.xsd.xml` | Pagos 2.0 catalogue enumerations | `http://www.sat.gob.mx/sitio_internet/cfd/catalogos/Pagos`; imported by `Pagos20.xsd` |
| `Anexo20_2022.pdf` | Normative CFDI 4.0 technical standard (DOF 2022-01-13) | Field semantics; sealing algorithm (§ "Generación de sellos digitales"); cadena original construction rules |
| `Anexo_20_Guia_de_llenado_CFDI.pdf` | Fill-in guide for CFDI 4.0 | Field-level semantics beyond the structural XSD |
| `MatrizDeErrores_CFDI_v40_20260325.xls` | Official validation/error matrix | Business-rule reference (deferred; XSD-first per BR precedent) |
| `Guia_llenado_pagos.pdf` | Fill-in guide for Complemento de Pagos 2.0 | Phase-1 Pagos semantics |
| `Guia_complemento_Comercio_Exterior.pdf` | Comercio Exterior complement guide | Out of Phase 1 — kept for a later phase |
| `Guia_llenadoCFDI_DPA.pdf` | "Otros derechos e impuestos" (DPA — Contribuciones, Derechos, Productos y Aprovechamientos collected by Federación/Entidades/Municipios) complement guide. Title verified directly from the PDF's own cover page — **not** the Donativos (Donatarias) complemento, a distinct SAT complemento this bundle does not cover; a prior version of this file mislabeled it "Donativos/DPA" | Out of Phase 1 — kept for a later phase |
| `Guia_llenado_CFDI_global.pdf` | Factura global (simplified/aggregate receipts) guide | Out of Phase 1 — kept for a later phase |
| `Guia_llenado_Nomina.pdf` | Complemento de Nómina 1.2 guide | Out of Phase 1 — kept for a later phase |

## Pending specs

| Document | Status | Notes |
|---|---|---|
| SAT catálogos page canonical URL | `[NEED:]` | Blocks the `Sources and versions` row above from moving from `manual` to `fetch`/`search` in the regulatory watch |
| SAT matriz de errores page canonical URL | `[NEED:]` | Same |
| RMF vigente / Anexo 20 DOF page canonical URL | `[NEED:]` | Currently tracked `manual` in `context-library/regulatory-watch/sources.md` |
| CSD issuance documentation (`.cer`/`.key` container format) | `[NEED:]` | `mcp_einvoicing_core.digital_signature.SelloDigitalSigner` assumes an encrypted PKCS#8 DER `.key`, matching common third-party CFDI tooling, but no supplied SAT document confirms this — flagged `[Unverified]` in that class's docstring |
| PAC web-service specification | `[NEED: out of Phase 1]` | Deferred; no vendor spec supplied. Tracked in `context-library/roadmap-2026.md`. |
| Remaining ~33 cadena original `xsl:include` fragments (Carta Porte, Nómina, Comercio Exterior, etc.) | `[NEED: only if scope expands past Phase 1]` | Safely stubbed for now since their templates are never reached by a Phase-1 document |

## Non-file sources

Not every source is a downloadable file. The three authority URLs marked "user-supplied;
not independently fetched" above were provided by the user in chat rather than retrieved by
an agent, per the bundled-sources-only research policy — no local file backs them beyond
this table entry, and their content is already folded into
`context-library/countries/mx.md`.
