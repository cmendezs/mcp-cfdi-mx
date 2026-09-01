"""mx__validate_cfdi — XSD validation against cfdv40.xsd (+ TFD 1.1, + Pagos 2.0)."""

from __future__ import annotations

from typing import Annotated

from lxml import etree
from mcp_einvoicing_core.xml_utils import safe_fromstring

from mcp_cfdi_mx.utils.xsd_validator import (
    cfdi_validator,
    full_validator,
    pagos_validator,
    tfd_validator,
)

_TFD_NS = "http://www.sat.gob.mx/TimbreFiscalDigital"
_PAGO20_NS = "http://www.sat.gob.mx/Pagos20"


def mx__validate_cfdi(
    xml: Annotated[str, "The CFDI 4.0 Comprobante XML to validate, as a string"],
) -> dict[str, object]:
    """Validate a CFDI 4.0 document against the official SAT XSD schemas.

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
    """
    xml_bytes = xml.encode("utf-8")

    try:
        root = safe_fromstring(xml_bytes)
    except (etree.XMLSyntaxError, ValueError) as exc:
        return {"valid": False, "error": "xml_parse_error", "details": str(exc)}

    result: dict[str, object] = {}
    all_valid = True

    tfd_el = root.find(f".//{{{_TFD_NS}}}TimbreFiscalDigital")
    pagos_el = root.find(f".//{{{_PAGO20_NS}}}Pagos")

    # A Comprobante carrying a Complemento must be validated with that
    # complement's schema loaded too (Complemento's xs:any wildcard is
    # strict) — see xsd_validator.cfdi_validator()'s docstring.
    if tfd_el is not None or pagos_el is not None:
        comprobante_validator = full_validator(
            include_tfd=tfd_el is not None, include_pagos=pagos_el is not None
        )
    else:
        comprobante_validator = cfdi_validator()

    comprobante_result = comprobante_validator.validate(xml_bytes, profile="cfdi40")
    result["comprobante"] = comprobante_result.to_dict()
    all_valid = all_valid and comprobante_result.is_valid

    if tfd_el is not None:
        tfd_bytes = etree.tostring(tfd_el, xml_declaration=True, encoding="UTF-8")
        tfd_result = tfd_validator().validate(tfd_bytes, profile="tfd11")
        result["tfd"] = tfd_result.to_dict()
        all_valid = all_valid and tfd_result.is_valid

    if pagos_el is not None:
        pagos_bytes = etree.tostring(pagos_el, xml_declaration=True, encoding="UTF-8")
        pagos_result = pagos_validator().validate(pagos_bytes, profile="pagos20")
        result["pagos"] = pagos_result.to_dict()
        all_valid = all_valid and pagos_result.is_valid

    result["valid"] = all_valid
    return result
