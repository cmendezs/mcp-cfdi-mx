# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.3.0] - 2026-09-03

Remediates the findings from the first Mexico country audit
(`audit/2026-09-audit-mx.md`, v0.2.0). Every fix narrows a model/tool rule that
previously allowed the tools to silently emit XSD-invalid or PAC-rejected
output; existing valid input is unaffected.

### Changed
- **MX-SC-1** — `CFDIComprobante.date` now enforces the `t_FechaH` datetime
  pattern (`AAAA-MM-DDThh:mm:ss`, `tdCFDI.xsd`). A date-only value (e.g.
  `"2026-09-01"`) is now rejected at construction time instead of producing
  an XSD-invalid `Fecha`.
- **MX-SC-2** — `MXEmisor.name`/`MXReceptor.name` are now required and
  non-empty (`minLength=1, maxLength=300`, `Nombre`, `cfdv40.xsd.xml`). A
  missing or empty party name is now rejected instead of emitting an empty
  `Nombre` attribute.
- **MX-SC-3** — `mx__build_pago` now forces `buyer.uso_cfdi="CP01"`,
  mirroring how it already forces `SubTotal`/`Moneda`/etc. — a Pagos CFDI is
  always emitted with the schema-mandated `UsoCFDI`, regardless of what the
  caller passed.
- **MX-TC-1** — `CFDIComprobante` now enforces the generic-RFC cross-
  constraint: a receptor RFC of `XAXX010101000` or `XEXX010101000` must pair
  with `regimen_fiscal_receptor="616"`, and — on non-Pago CFDIs — with
  `uso_cfdi="S01"` (Pago CFDIs are exempt, since `UsoCFDI` is unconditionally
  `"CP01"` there). Verified directly against `Anexo20_2022.pdf` and
  `Anexo_20_Guia_de_llenado_CFDI.pdf` during remediation — both generic RFCs
  pair with regimen `616` (corrects a prior `context-library/countries/mx.md`
  note that had claimed `610` for `XEXX010101000`, which does not appear in
  either source document).
- **MX-SC-4** — `PagoDoctoRelacionado` now enforces
  `ImpSaldoAnt == ImpPagado + ImpSaldoInsoluto` (exact `Decimal` comparison),
  per `Guia_llenado_pagos.pdf`'s `ImpSaldoInsoluto` field rule.

### Fixed
- **MX-DOC-1** — no code change; `context-library/countries/mx.md`'s
  `c_Impuesto` catalogue table was corrected from its display-column form
  (`1`/`2`/`3`) to the XSD emission form (`001`/`002`/`003`), matching what
  `ConceptoImpuesto`'s docstring already documented correctly.

## [0.2.0] - 2026-09-01

### Added
- `mx__build_cfdi` — build a well-formed, unsealed CFDI 4.0 `Comprobante` XML (Ingreso or
  Egreso), including document-level `Impuestos` aggregated from concept-level taxes.
- `mx__build_pago` — build a Complemento de Pagos 2.0 CFDI (`TipoDeComprobante="P"`), composing
  the fixed single-`Concepto` wrapper SAT's Guía de llenado de pagos mandates.
- `mx__validate_cfdi` — full XSD validation against `cfdv40.xsd`, plus
  `TimbreFiscalDigitalv11.xsd.xml`/`Pagos20.xsd.xml` when those complements are present. Resolves
  SAT's absolute-URL schema imports through a local resolver, and compiles a combined schema when
  complements are present (`Complemento`'s `xs:any` wildcard is strict).
- `mx__seal_cfdi` — `sealing_mode`-aware (`"local"` \| `"pac"`) wrapper around core's
  `SelloDigitalSigner` (core v1.30.0).
- `mx__verify_tfd` — parse a PAC-returned Timbre Fiscal Digital 1.1 stamp and, when the PAC's
  certificate is supplied, cryptographically verify `SelloSAT`.
- `README.es-MX.md` Spanish translation.
- 65 tests covering models, XML builders, XSD validators, and all five new tools, including a
  full build → seal → verify → XSD-validate round trip and TFD tamper-detection.

### Fixed
- `Pagos20.totales` was incorrectly optional — `Pagos20.xsd.xml`'s `Totales` element has no
  `minOccurs="0"` and is required.

## [0.1.0] - 2026-09-01

### Added
- Initial scaffold: `CFDIComprobante`/`MXEmisor`/`MXReceptor`/`CFDIConcepto` models
  (CFDI 4.0 Ingreso/Egreso) and `Pagos20` models (Complemento de Pagos 2.0), both
  traced to the supplied SAT Anexo 20 spec bundle under `specs/`.
- RFC validation via `mcp-einvoicing-core`'s `TaxIdentifier.validate_mx_rfc` (core v1.29.0).
- `mx__get_supported_scope` MCP tool.
- Not yet implemented: CFDI generation/validation/sealing/TFD-verification tools
  (`mx__build_cfdi`, `mx__build_pago`, `mx__validate_cfdi`, `mx__seal_cfdi`,
  `mx__verify_tfd`) — tracked in `context-library/roadmap-2026.md`.
