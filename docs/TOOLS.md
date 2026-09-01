# Tool reference — `mcp_cfdi_mx`

This file is generated from the MCP server's tool registry by `scripts/gen_tool_reference.py`. Do not edit it by hand; run the script instead.

**Tools:** 6

## `mx__build_cfdi`

Build a well-formed, unsealed CFDI 4.0 `Comprobante` XML (Ingreso or Egreso).

`comprobante_data` is validated against `CFDIComprobante` — see that
model for the full field list (`seller`/`buyer` as `MXEmisor`/
`MXReceptor`, `lines` as `CFDIConcepto`, `tipo_de_comprobante`, etc.).
RFC fields are validated via `TaxIdentifier.validate_mx_rfc` as part of
model construction; a malformed RFC is reported as a validation error,
not a generated document.

The output XML omits `Sello`/`NoCertificado`/`Certificado` — those three
schema-required attributes are populated by `mx__seal_cfdi`, run
afterward. `mx__validate_cfdi` run on this output is expected to report
exactly those three attributes missing; that is not a bug in this tool.

For `TipoDeComprobante="P"` (Complemento de Pagos), use `mx__build_pago`
instead — this tool only builds Ingreso/Egreso Comprobantes.

Returns a dict with:
- ``xml``: the generated, unsealed CFDI 4.0 XML string
- ``total``: the computed `Total` attribute (SubTotal - Descuento +
  traslados - retenciones)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `comprobante_data` | object | yes |  | Fields matching the CFDIComprobante schema (Ingreso or Egreso only) |

## `mx__build_pago`

Build a well-formed, unsealed Complemento de Pagos 2.0 CFDI.

Composes the fixed single-`Concepto` wrapper SAT's Guía de llenado de
pagos mandates for a Pago-type `Comprobante` (`ClaveProdServ`,
`ClaveUnidad`, `Descripcion`, `ValorUnitario`, `Importe`, `ObjetoImp` are
all fixed conventional values — see this module's docstring constants)
with the `Pagos20` complement built from `pagos_data`, and attaches the
complement under `cfdi:Complemento`.

`comprobante_data` must set `buyer.uso_cfdi="CP01"` (the schema requires
it for Pagos CFDIs per the same guide) — not forced here since it is a
receptor-level field the caller controls, but a mismatch is a caller
error, not something this tool silently corrects.

The output XML omits `Sello`/`NoCertificado`/`Certificado`, same as
`mx__build_cfdi` — seal afterward with `mx__seal_cfdi`.

Returns a dict with:
- ``xml``: the generated, unsealed CFDI XML string (with the Pagos
  complement attached)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `comprobante_data` | object | yes |  | Fields matching CFDIComprobante, minus SubTotal/Moneda/FormaPago/MetodoPago/CondicionesDePago/lines/TipoDeComprobante — all fixed or derived for a Pagos CFDI, do not supply them |
| `pagos_data` | object | yes |  | Fields matching the Pagos20 schema |

## `mx__get_supported_scope`

Return the CFDI document types, complementos, and sealing modes this package supports.

Reflects Phase 1 scope locked in context-library/countries/mx.md
(workspace root repo): CFDI 4.0 Ingreso + Egreso + Complemento de Pagos
2.0, PAC-agnostic sealing. Build (`mx__build_cfdi`/`mx__build_pago`),
XSD validation (`mx__validate_cfdi`), sealing (`mx__seal_cfdi`), and TFD
verification (`mx__verify_tfd`) are all implemented. PAC submission
transport and later-phase complementos are not — see roadmap-2026.md.

Returns:
    A `ScopeInfo` describing current scope, for callers to check before
    assuming a document type or complemento is supported.

_No parameters._

## `mx__seal_cfdi`

Seal (or deliberately not seal) a CFDI 4.0 Comprobante, PAC-agnostic.

`sealing_mode="local"` computes the cadena original via the actual SAT
XSLT transform (`specs/cadenaoriginal_4_0.xslt`, with its `utilerias.xslt`
and `Pagos20.xslt` includes resolved from `specs/`; any other complemento
include a document might reference is not in Phase-1 scope and stubs to
a no-op template — see `SelloDigitalSigner`'s docstring), then computes
`Sello`/`NoCertificado`/`Certificado` via
`mcp_einvoicing_core.digital_signature.SelloDigitalSigner` — no local
reimplementation of the signing algorithm.

`sealing_mode="pac"` returns *xml* unchanged: some PACs accept an
unsealed, schema-valid CFDI and seal it on the emisor's behalf. This
tool does not submit to any PAC — see the package README for the
PAC-agnostic design.

CSD key material is always a file path, never accepted as plaintext key
content in a tool argument.

Returns a dict with:
- ``xml``: the sealed (or, for ``"pac"``, unchanged) XML string
- ``sealing_mode``: echoes the mode used

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `xml` | string | yes |  | The unsealed CFDI 4.0 Comprobante XML, as returned by mx__build_cfdi/mx__build_pago |
| `sealing_mode` | string | yes |  | 'local': compute Sello/NoCertificado/Certificado from the supplied CSD. 'pac': return the XML unchanged, for a PAC that seals on the emisor's behalf. |
| `cert_path` | string | null | no | `None` | Path to the CSD's DER-encoded certificate (.cer). Required when sealing_mode='local'. |
| `key_path` | string | null | no | `None` | Path to the CSD's encrypted PKCS#8 DER private key (.key). Required when sealing_mode='local'. |
| `key_password` | string | null | no | `None` | Passphrase for the private key. Required when sealing_mode='local'. |
| `no_certificado` | string | null | no | `None` | The CSD's 20-digit serial number from the SAT enrollment acknowledgment (acuse). Not derived from the certificate bytes — no confirmed algorithm exists for that derivation, see SelloDigitalSigner's docstring. Required when sealing_mode='local'. |

## `mx__validate_cfdi`

Validate a CFDI 4.0 document against the official SAT XSD schemas.

Always validates the root `Comprobante` against `cfdv40.xsd`. If a
`TimbreFiscalDigital` complement is present (i.e. the document has been
stamped by a PAC), it is additionally validated against
`TimbreFiscalDigitalv11.xsd.xml`. If a `Pagos` complement is present
(`TipoDeComprobante="P"`), it is additionally validated against
`Pagos20.xsd.xml`.

This is XSD-only — business-rule checks from SAT's Matriz de errores
(`specs/MatrizDeErrores_CFDI_v40_20260325.xls`) are not run, mirroring
`mcp-nfe-br`'s `br__validate_nfe_xml` precedent (XSD-first, business
rules deferred). A document that passes this validator is structurally
conformant but not guaranteed to pass PAC certification.

Returns a dict with:
- ``valid``: True only if every schema that applies passed
- ``comprobante``: the `cfdv40.xsd` validation result
- ``tfd``: the TFD validation result, present only if a
  `TimbreFiscalDigital` element was found
- ``pagos``: the Pagos 2.0 validation result, present only if a
  `Pagos` element was found

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `xml` | string | yes |  | The CFDI 4.0 Comprobante XML to validate, as a string |

## `mx__verify_tfd`

Parse a Timbre Fiscal Digital 1.1 stamp and, optionally, verify SelloSAT.

Always returns the TFD's own attributes (`UUID`, `FechaTimbrado`,
`RfcProvCertif`, `SelloCFD`, `NoCertificadoSAT`, `SelloSAT`, ...) and the
recomputed cadena original (via `cadenaoriginal_TFD_1_1.xslt`, per
Anexo 20 Rubro III.B). If `pac_certificado_der_b64` is supplied,
additionally verifies `SelloSAT` (SHA-256 + RSA-PKCS#1v1.5, the same
algorithm as the emisor's own Sello) against that certificate's public
key. Without it, `sello_sat_verified` is `null` — parsing succeeded but
cryptographic verification was not attempted, not "passed".

Returns a dict with:
- ``found``: False if no `TimbreFiscalDigital` element exists in *xml*
- ``fields``: the TFD's own attributes
- ``cadena_original``: the recomputed cadena original string
- ``sello_sat_verified``: True/False if `pac_certificado_der_b64` was
  supplied, else null

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `xml` | string | yes |  | The sealed, PAC-stamped CFDI XML (with a TimbreFiscalDigital complement) |
| `pac_certificado_der_b64` | string | null | no | `None` | Base64-encoded DER certificate of the PAC/SAT that stamped this TFD, used to cryptographically verify SelloSAT. SAT does not embed this certificate in the TFD itself, so it is not available without the caller supplying it. Omit to parse fields and compute the cadena original without verifying SelloSAT. |
