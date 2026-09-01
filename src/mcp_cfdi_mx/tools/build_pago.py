"""mx__build_pago — build a Complemento de Pagos 2.0 CFDI (TipoDeComprobante=P)."""

from __future__ import annotations

from typing import Annotated, Any

from lxml import etree
from pydantic import ValidationError

from mcp_cfdi_mx.models.invoice import CFDIComprobante, TipoDeComprobante
from mcp_cfdi_mx.models.pagos import Pagos20
from mcp_cfdi_mx.utils.pagos_builder import build_pagos
from mcp_cfdi_mx.utils.xml_builder import CFDI_NS, build_comprobante

# Fixed Concepto values for a Pago-type CFDI, confirmed verbatim against
# specs/Guia_llenado_pagos.pdf ("Nodo: Conceptos / Nodo: Concepto" section):
# ClaveProdServ=84111506, NoIdentificacion/Unidad/Descuento must not exist,
# Cantidad=1, ClaveUnidad=ACT, Descripcion=Pago, ValorUnitario=0, Importe=0,
# ObjetoImp=01, and the Concepto's own Impuestos node must not exist.
_PAGO_CONCEPTO_DEFAULTS = {
    "clave_prod_serv": "84111506",
    "clave_unidad": "ACT",
    "description": "Pago",
    "quantity": 1,
    "unit_price": 0,
    "total_price": 0,
    "objeto_imp": "01",
    "line_number": 1,
    "vat_rate": 0,
}

# Comprobante-level fixed values for TipoDeComprobante=P, confirmed against
# the same guide ("Cero en el campo Total sin registrar dato alguno en los
# campos MetodoPago y FormaPago"; SubTotal=0; Moneda=XXX).
_PAGO_COMPROBANTE_FIXED = {
    "sub_total": "0",
    "currency": "XXX",
    "forma_pago": None,
    "metodo_pago": None,
    "condiciones_de_pago": None,
}


def mx__build_pago(
    comprobante_data: Annotated[
        dict[str, Any],
        (
            "Fields matching CFDIComprobante, minus SubTotal/Moneda/FormaPago/"
            "MetodoPago/CondicionesDePago/lines/TipoDeComprobante — all fixed "
            "or derived for a Pagos CFDI, do not supply them"
        ),
    ],
    pagos_data: Annotated[dict[str, Any], "Fields matching the Pagos20 schema"],
) -> dict[str, object]:
    """Build a well-formed, unsealed Complemento de Pagos 2.0 CFDI.

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
    """
    merged = {
        **comprobante_data,
        **_PAGO_COMPROBANTE_FIXED,
        "tipo_de_comprobante": TipoDeComprobante.PAGO,
        "lines": [dict(_PAGO_CONCEPTO_DEFAULTS)],
    }
    try:
        comprobante = CFDIComprobante.model_validate(merged)
    except ValidationError as exc:
        return {"error": "validation_error", "details": exc.errors(), "field": "comprobante_data"}

    try:
        pagos = Pagos20.model_validate(pagos_data)
    except ValidationError as exc:
        return {"error": "validation_error", "details": exc.errors(), "field": "pagos_data"}

    root = build_comprobante(comprobante)
    complemento_el = etree.SubElement(root, f"{{{CFDI_NS}}}Complemento")
    complemento_el.append(build_pagos(pagos))

    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    return {"xml": xml_bytes.decode("utf-8")}
