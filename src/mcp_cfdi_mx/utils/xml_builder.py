"""Build CFDI 4.0 `Comprobante` XML from `CFDIComprobante` (`cfdv40.xsd.xml`).

Element/attribute names, order, and cardinality are traced directly to the
supplied `specs/cfdv40.xsd.xml` — see that file's `Comprobante`/`Concepto`
`xs:sequence` declarations for the authoritative source. `Sello`,
`NoCertificado`, and `Certificado` are intentionally **not** emitted here —
those three are required by the schema but populated by
`mcp_einvoicing_core.digital_signature.SelloDigitalSigner` after this build
step (see `tools/seal.py`). A document from this builder is well-formed XML
but not yet XSD-valid until sealed; validating it before sealing is expected
to report those three attributes missing.
"""

from __future__ import annotations

from collections import OrderedDict
from decimal import Decimal

from lxml import etree

from mcp_cfdi_mx.models.invoice import CFDIComprobante, CFDIConcepto, ConceptoImpuesto

CFDI_NS = "http://www.sat.gob.mx/cfd/4"
_XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
_SCHEMA_LOCATION = (
    "http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd"
)


def _q(local: str) -> str:
    return f"{{{CFDI_NS}}}{local}"


def _set_optional(element: etree._Element, attr: str, value: str | None) -> None:
    if value is not None:
        element.set(attr, value)


def _sum_amounts(values: list[str | None]) -> str:
    total = sum((Decimal(v) for v in values if v is not None), start=Decimal("0"))
    return str(total)


def _build_traslado_or_retencion(local: str, tax: ConceptoImpuesto) -> etree._Element:
    el = etree.Element(_q(local))
    el.set("Base", tax.base)
    el.set("Impuesto", tax.impuesto)
    el.set("TipoFactor", tax.tipo_factor)
    _set_optional(el, "TasaOCuota", tax.tasa_o_cuota)
    _set_optional(el, "Importe", tax.importe)
    return el


def _build_concepto(concepto: CFDIConcepto) -> etree._Element:
    el = etree.Element(_q("Concepto"))

    if concepto.traslados or concepto.retenciones:
        impuestos_el = etree.SubElement(el, _q("Impuestos"))
        if concepto.traslados:
            traslados_el = etree.SubElement(impuestos_el, _q("Traslados"))
            for t in concepto.traslados:
                traslados_el.append(_build_traslado_or_retencion("Traslado", t))
        if concepto.retenciones:
            retenciones_el = etree.SubElement(impuestos_el, _q("Retenciones"))
            for r in concepto.retenciones:
                retenciones_el.append(_build_traslado_or_retencion("Retencion", r))

    el.set("ClaveProdServ", concepto.clave_prod_serv)
    el.set("Cantidad", str(concepto.quantity if concepto.quantity is not None else 1))
    el.set("ClaveUnidad", concepto.clave_unidad)
    _set_optional(el, "Unidad", concepto.unit_of_measure)
    el.set("Descripcion", concepto.description)
    el.set("ValorUnitario", str(concepto.unit_price))
    el.set("Importe", str(concepto.total_price))
    el.set("ObjetoImp", concepto.objeto_imp)
    return el


def _build_document_impuestos(conceptos: list[CFDIConcepto]) -> etree._Element | None:
    """Aggregate `Impuestos` at document level from every concept's own taxes.

    Retenciones sum `Importe` grouped by `Impuesto` only (the schema's
    document-level `Retencion` carries no `TipoFactor`/`TasaOCuota`).
    Traslados sum `Base`/`Importe` grouped by `(Impuesto, TipoFactor,
    TasaOCuota)` (the schema's document-level `Traslado` carries all three
    as grouping keys, per `cfdv40.xsd.xml`'s own documentation for that
    element: "agrupado por impuesto, TipoFactor y TasaOCuota").
    """
    retencion_groups: OrderedDict[str, list[str | None]] = OrderedDict()
    traslado_groups: OrderedDict[tuple[str, str, str | None], dict[str, list[str | None]]] = (
        OrderedDict()
    )

    for concepto in conceptos:
        for r in concepto.retenciones:
            retencion_groups.setdefault(r.impuesto, []).append(r.importe)
        for t in concepto.traslados:
            key = (t.impuesto, t.tipo_factor, t.tasa_o_cuota)
            group = traslado_groups.setdefault(key, {"base": [], "importe": []})
            group["base"].append(t.base)
            group["importe"].append(t.importe)

    if not retencion_groups and not traslado_groups:
        return None

    impuestos_el = etree.Element(_q("Impuestos"))

    if retencion_groups:
        total_retenciones = _sum_amounts(
            [amt for amounts in retencion_groups.values() for amt in amounts]
        )
        impuestos_el.set("TotalImpuestosRetenidos", total_retenciones)
        retenciones_el = etree.SubElement(impuestos_el, _q("Retenciones"))
        for impuesto, amounts in retencion_groups.items():
            r_el = etree.SubElement(retenciones_el, _q("Retencion"))
            r_el.set("Impuesto", impuesto)
            r_el.set("Importe", _sum_amounts(amounts))

    if traslado_groups:
        total_traslados = _sum_amounts(
            [amt for group in traslado_groups.values() for amt in group["importe"]]
        )
        impuestos_el.set("TotalImpuestosTrasladados", total_traslados)
        traslados_el = etree.SubElement(impuestos_el, _q("Traslados"))
        for (impuesto, tipo_factor, tasa_o_cuota), group in traslado_groups.items():
            t_el = etree.SubElement(traslados_el, _q("Traslado"))
            t_el.set("Base", _sum_amounts(group["base"]))
            t_el.set("Impuesto", impuesto)
            t_el.set("TipoFactor", tipo_factor)
            _set_optional(t_el, "TasaOCuota", tasa_o_cuota)
            if any(v is not None for v in group["importe"]):
                t_el.set("Importe", _sum_amounts(group["importe"]))

    return impuestos_el


def build_comprobante(comprobante: CFDIComprobante) -> etree._Element:
    """Return the `cfdi:Comprobante` root element for *comprobante*.

    Does not serialize to bytes — callers needing bytes should use
    `build_comprobante_xml`. Kept separate so `tools/build_pago.py` can
    append the `Complemento`/`Pagos` element before serialization.
    """
    root = etree.Element(
        _q("Comprobante"),
        nsmap={"cfdi": CFDI_NS, "xsi": _XSI_NS},
    )
    root.set(f"{{{_XSI_NS}}}schemaLocation", _SCHEMA_LOCATION)

    root.set("Version", comprobante.version)
    _set_optional(root, "Serie", comprobante.serie)
    _set_optional(root, "Folio", comprobante.folio)
    root.set("Fecha", comprobante.date)
    # Sello/NoCertificado/Certificado: populated by mx__seal_cfdi, not here.
    _set_optional(root, "FormaPago", comprobante.forma_pago)
    _set_optional(root, "CondicionesDePago", comprobante.condiciones_de_pago)
    root.set("SubTotal", comprobante.sub_total)
    _set_optional(root, "Descuento", comprobante.descuento)
    root.set("Moneda", comprobante.currency)
    _set_optional(root, "TipoCambio", comprobante.tipo_cambio)
    root.set("Total", _comprobante_total(comprobante))
    root.set("TipoDeComprobante", comprobante.tipo_de_comprobante.value)
    root.set("Exportacion", comprobante.exportacion)
    _set_optional(
        root, "MetodoPago", comprobante.metodo_pago.value if comprobante.metodo_pago else None
    )
    root.set("LugarExpedicion", comprobante.lugar_expedicion)
    _set_optional(root, "Confirmacion", comprobante.confirmacion)

    if comprobante.cfdi_relacionados:
        by_tipo: OrderedDict[str, list[str]] = OrderedDict()
        for rel in comprobante.cfdi_relacionados:
            by_tipo.setdefault(rel.tipo_relacion, []).append(rel.uuid)
        for tipo_relacion, uuids in by_tipo.items():
            group_el = etree.SubElement(root, _q("CfdiRelacionados"))
            group_el.set("TipoRelacion", tipo_relacion)
            for uuid in uuids:
                rel_el = etree.SubElement(group_el, _q("CfdiRelacionado"))
                rel_el.set("UUID", uuid)

    emisor_el = etree.SubElement(root, _q("Emisor"))
    emisor_el.set("Rfc", comprobante.seller.tax_id.identifier)
    emisor_el.set("Nombre", comprobante.seller.name)
    emisor_el.set("RegimenFiscal", comprobante.seller.regimen_fiscal)

    receptor_el = etree.SubElement(root, _q("Receptor"))
    receptor_el.set("Rfc", comprobante.buyer.tax_id.identifier)
    receptor_el.set("Nombre", comprobante.buyer.name)
    receptor_el.set("DomicilioFiscalReceptor", comprobante.buyer.domicilio_fiscal_receptor)
    receptor_el.set("RegimenFiscalReceptor", comprobante.buyer.regimen_fiscal_receptor)
    receptor_el.set("UsoCFDI", comprobante.buyer.uso_cfdi)

    conceptos_el = etree.SubElement(root, _q("Conceptos"))
    for concepto in comprobante.lines:
        conceptos_el.append(_build_concepto(concepto))

    doc_impuestos_el = _build_document_impuestos(comprobante.lines)
    if doc_impuestos_el is not None:
        root.append(doc_impuestos_el)

    return root


def _comprobante_total(comprobante: CFDIComprobante) -> str:
    """`Total` is not independently supplied — it is SubTotal minus Descuento
    plus the sum of impuestos trasladados minus impuestos retenidos, per
    `cfdv40.xsd.xml`'s own documentation of the `Total` attribute."""
    total = Decimal(comprobante.sub_total)
    if comprobante.descuento is not None:
        total -= Decimal(comprobante.descuento)
    for concepto in comprobante.lines:
        for t in concepto.traslados:
            if t.importe is not None:
                total += Decimal(t.importe)
        for r in concepto.retenciones:
            if r.importe is not None:
                total -= Decimal(r.importe)
    return str(total)


def build_comprobante_xml(comprobante: CFDIComprobante) -> bytes:
    """Return the serialized, unsealed `Comprobante` XML for *comprobante*."""
    root = build_comprobante(comprobante)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")
