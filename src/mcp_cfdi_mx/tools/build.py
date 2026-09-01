"""mx__build_cfdi — build a CFDI 4.0 Ingreso/Egreso Comprobante from structured input."""

from __future__ import annotations

from typing import Annotated, Any

from lxml import etree
from pydantic import ValidationError

from mcp_cfdi_mx.models.invoice import CFDIComprobante
from mcp_cfdi_mx.utils.xml_builder import build_comprobante


def mx__build_cfdi(
    comprobante_data: Annotated[
        dict[str, Any], "Fields matching the CFDIComprobante schema (Ingreso or Egreso only)"
    ],
) -> dict[str, object]:
    """Build a well-formed, unsealed CFDI 4.0 `Comprobante` XML (Ingreso or Egreso).

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
    """
    try:
        comprobante = CFDIComprobante.model_validate(comprobante_data)
    except ValidationError as exc:
        return {"error": "validation_error", "details": exc.errors()}

    if comprobante.tipo_de_comprobante.value == "P":
        return {
            "error": "wrong_tool",
            "details": (
                "TipoDeComprobante='P' (Complemento de Pagos) must be built with mx__build_pago."
            ),
        }

    root = build_comprobante(comprobante)
    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8")

    return {"xml": xml_bytes.decode("utf-8"), "total": root.get("Total")}
