"""Tests for mcp_cfdi_mx.utils.xml_builder."""

from __future__ import annotations

from lxml import etree

from mcp_cfdi_mx.models.invoice import CFDIComprobante, CfdiRelacionado
from mcp_cfdi_mx.utils.xml_builder import CFDI_NS, build_comprobante_xml
from mcp_cfdi_mx.utils.xsd_validator import cfdi_validator


def _q(local: str) -> str:
    return f"{{{CFDI_NS}}}{local}"


class TestBuildComprobante:
    def test_root_element_and_namespace(self, comprobante_ingreso: CFDIComprobante) -> None:
        xml = build_comprobante_xml(comprobante_ingreso)
        root = etree.fromstring(xml)
        assert root.tag == _q("Comprobante")

    def test_required_attributes_present(self, comprobante_ingreso: CFDIComprobante) -> None:
        xml = build_comprobante_xml(comprobante_ingreso)
        root = etree.fromstring(xml)
        assert root.get("Version") == "4.0"
        assert root.get("SubTotal") == "100.00"
        assert root.get("Total") == "100.00"
        assert root.get("TipoDeComprobante") == "I"
        assert root.get("LugarExpedicion") == "06600"

    def test_sello_and_friends_omitted(self, comprobante_ingreso: CFDIComprobante) -> None:
        xml = build_comprobante_xml(comprobante_ingreso)
        root = etree.fromstring(xml)
        assert root.get("Sello") is None
        assert root.get("NoCertificado") is None
        assert root.get("Certificado") is None

    def test_emisor_receptor(self, comprobante_ingreso: CFDIComprobante) -> None:
        root = etree.fromstring(build_comprobante_xml(comprobante_ingreso))
        emisor_el = root.find(_q("Emisor"))
        assert emisor_el.get("Rfc") == "AAA010101AA1"
        assert emisor_el.get("RegimenFiscal") == "601"
        receptor_el = root.find(_q("Receptor"))
        assert receptor_el.get("Rfc") == "XAXX010101000"
        assert receptor_el.get("UsoCFDI") == "S01"

    def test_concepto_present(self, comprobante_ingreso: CFDIComprobante) -> None:
        root = etree.fromstring(build_comprobante_xml(comprobante_ingreso))
        conceptos = root.findall(f"{_q('Conceptos')}/{_q('Concepto')}")
        assert len(conceptos) == 1
        assert conceptos[0].get("ClaveProdServ") == "84111506"

    def test_total_includes_traslado(self, comprobante_con_iva: CFDIComprobante) -> None:
        root = etree.fromstring(build_comprobante_xml(comprobante_con_iva))
        assert root.get("SubTotal") == "100.00"
        assert root.get("Total") == "116.00"

    def test_document_level_impuestos_aggregated(
        self, comprobante_con_iva: CFDIComprobante
    ) -> None:
        root = etree.fromstring(build_comprobante_xml(comprobante_con_iva))
        impuestos_el = root.find(_q("Impuestos"))
        assert impuestos_el is not None
        assert impuestos_el.get("TotalImpuestosTrasladados") == "16.00"
        traslado_el = impuestos_el.find(f"{_q('Traslados')}/{_q('Traslado')}")
        assert traslado_el.get("Base") == "100.00"
        assert traslado_el.get("Impuesto") == "002"

    def test_cfdi_relacionados_grouped_by_tipo(self, emisor, receptor, concepto) -> None:
        comprobante = CFDIComprobante(
            document_type="E",
            date="2026-09-01T12:00:00",
            number="NC-1",
            seller=emisor,
            buyer=receptor,
            lines=[concepto],
            tipo_de_comprobante="E",
            lugar_expedicion="06600",
            sub_total="100.00",
            cfdi_relacionados=[
                CfdiRelacionado(uuid="12345678-1234-1234-1234-123456789012", tipo_relacion="01"),
                CfdiRelacionado(uuid="87654321-4321-4321-4321-210987654321", tipo_relacion="01"),
            ],
        )
        root = etree.fromstring(build_comprobante_xml(comprobante))
        groups = root.findall(_q("CfdiRelacionados"))
        assert len(groups) == 1
        assert groups[0].get("TipoRelacion") == "01"
        assert len(groups[0].findall(_q("CfdiRelacionado"))) == 2

    def test_unsealed_output_fails_xsd_only_on_sealing_attrs(
        self, comprobante_ingreso: CFDIComprobante
    ) -> None:
        xml = build_comprobante_xml(comprobante_ingreso)
        result = cfdi_validator().validate(xml, profile="cfdi40")
        assert result.is_valid is False
        error_texts = " ".join(e.text for e in result.errors)
        for attr in ("Sello", "NoCertificado", "Certificado"):
            assert f"'{attr}'" in error_texts
