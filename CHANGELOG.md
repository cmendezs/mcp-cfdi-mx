# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

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
