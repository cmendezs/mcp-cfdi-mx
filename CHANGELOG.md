# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

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
