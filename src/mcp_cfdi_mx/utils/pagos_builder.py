"""Build a Complemento de Pagos 2.0 `pago20:Pagos` element from `Pagos20` (`Pagos20.xsd.xml`).

Element/attribute names and order are traced directly to the supplied
`specs/Pagos20.xsd.xml` — see that file's `Pagos`/`Pago`/`DoctoRelacionado`
`xs:sequence` declarations for the authoritative source.
"""

from __future__ import annotations

from lxml import etree

from mcp_cfdi_mx.models.pagos import ImpuestoDR, ImpuestoP, Pago, PagoDoctoRelacionado, Pagos20

PAGO20_NS = "http://www.sat.gob.mx/Pagos20"


def _q(local: str) -> str:
    return f"{{{PAGO20_NS}}}{local}"


def _set_optional(element: etree._Element, attr: str, value: str | None) -> None:
    if value is not None:
        element.set(attr, value)


def _build_impuesto_dr(local: str, tax: ImpuestoDR) -> etree._Element:
    el = etree.Element(_q(local))
    el.set("BaseDR", tax.base_dr)
    el.set("ImpuestoDR", tax.impuesto_dr)
    el.set("TipoFactorDR", tax.tipo_factor_dr)
    _set_optional(el, "TasaOCuotaDR", tax.tasa_o_cuota_dr)
    _set_optional(el, "ImporteDR", tax.importe_dr)
    return el


def _build_impuesto_p(local: str, tax: ImpuestoP) -> etree._Element:
    el = etree.Element(_q(local))
    _set_optional(el, "BaseP", tax.base_p)
    el.set("ImpuestoP", tax.impuesto_p)
    _set_optional(el, "TipoFactorP", tax.tipo_factor_p)
    _set_optional(el, "TasaOCuotaP", tax.tasa_o_cuota_p)
    el.set("ImporteP", tax.importe_p)
    return el


def _build_docto_relacionado(docto: PagoDoctoRelacionado) -> etree._Element:
    el = etree.Element(_q("DoctoRelacionado"))

    if docto.traslados_dr or docto.retenciones_dr:
        impuestos_el = etree.SubElement(el, _q("ImpuestosDR"))
        if docto.retenciones_dr:
            retenciones_el = etree.SubElement(impuestos_el, _q("RetencionesDR"))
            for r in docto.retenciones_dr:
                retenciones_el.append(_build_impuesto_dr("RetencionDR", r))
        if docto.traslados_dr:
            traslados_el = etree.SubElement(impuestos_el, _q("TrasladosDR"))
            for t in docto.traslados_dr:
                traslados_el.append(_build_impuesto_dr("TrasladoDR", t))

    el.set("IdDocumento", docto.id_documento)
    _set_optional(el, "Serie", docto.serie)
    _set_optional(el, "Folio", docto.folio)
    el.set("MonedaDR", docto.moneda_dr)
    _set_optional(el, "EquivalenciaDR", docto.equivalencia_dr)
    el.set("NumParcialidad", docto.num_parcialidad)
    el.set("ImpSaldoAnt", docto.imp_saldo_ant)
    el.set("ImpPagado", docto.imp_pagado)
    el.set("ImpSaldoInsoluto", docto.imp_saldo_insoluto)
    el.set("ObjetoImpDR", docto.objeto_imp_dr)
    return el


def _build_pago(pago: Pago) -> etree._Element:
    el = etree.Element(_q("Pago"))

    for docto in pago.doctos_relacionados:
        el.append(_build_docto_relacionado(docto))

    if pago.traslados_p or pago.retenciones_p:
        impuestos_el = etree.SubElement(el, _q("ImpuestosP"))
        if pago.retenciones_p:
            retenciones_el = etree.SubElement(impuestos_el, _q("RetencionesP"))
            for r in pago.retenciones_p:
                retenciones_el.append(_build_impuesto_p("RetencionP", r))
        if pago.traslados_p:
            traslados_el = etree.SubElement(impuestos_el, _q("TrasladosP"))
            for t in pago.traslados_p:
                traslados_el.append(_build_impuesto_p("TrasladoP", t))

    el.set("FechaPago", pago.fecha_pago)
    el.set("FormaDePagoP", pago.forma_de_pago_p)
    el.set("MonedaP", pago.moneda_p)
    _set_optional(el, "TipoCambioP", pago.tipo_cambio_p)
    el.set("Monto", pago.monto)
    _set_optional(el, "NumOperacion", pago.num_operacion)
    _set_optional(el, "RfcEmisorCtaOrd", pago.rfc_emisor_cta_ord)
    _set_optional(el, "CtaOrdenante", pago.cta_ordenante)
    _set_optional(el, "RfcEmisorCtaBen", pago.rfc_emisor_cta_ben)
    _set_optional(el, "CtaBeneficiario", pago.cta_beneficiario)
    return el


def build_pagos(pagos: Pagos20) -> etree._Element:
    """Return the standalone `pago20:Pagos` element for *pagos*."""
    root = etree.Element(_q("Pagos"), nsmap={"pago20": PAGO20_NS})
    root.set("Version", pagos.version)

    t = pagos.totales
    totales_el = etree.SubElement(root, _q("Totales"))
    _set_optional(totales_el, "TotalRetencionesIVA", t.total_retenciones_iva)
    _set_optional(totales_el, "TotalRetencionesISR", t.total_retenciones_isr)
    _set_optional(totales_el, "TotalRetencionesIEPS", t.total_retenciones_ieps)
    _set_optional(totales_el, "TotalTrasladosBaseIVA16", t.total_traslados_base_iva16)
    _set_optional(totales_el, "TotalTrasladosImpuestoIVA16", t.total_traslados_impuesto_iva16)
    _set_optional(totales_el, "TotalTrasladosBaseIVA8", t.total_traslados_base_iva8)
    _set_optional(totales_el, "TotalTrasladosImpuestoIVA8", t.total_traslados_impuesto_iva8)
    _set_optional(totales_el, "TotalTrasladosBaseIVA0", t.total_traslados_base_iva0)
    _set_optional(totales_el, "TotalTrasladosImpuestoIVA0", t.total_traslados_impuesto_iva0)
    _set_optional(totales_el, "TotalTrasladosBaseIVAExento", t.total_traslados_base_iva_exento)
    totales_el.set("MontoTotalPagos", t.monto_total_pagos)

    for pago in pagos.pagos:
        root.append(_build_pago(pago))

    return root


def build_pagos_xml(pagos: Pagos20) -> bytes:
    """Return the serialized, standalone `pago20:Pagos` XML for *pagos*."""
    root = build_pagos(pagos)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")
