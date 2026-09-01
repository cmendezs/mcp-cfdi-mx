"""Tests for mcp_cfdi_mx.tools.seal (mx__seal_cfdi)."""

from __future__ import annotations

from lxml import etree

from mcp_cfdi_mx.models.invoice import CFDIComprobante
from mcp_cfdi_mx.tools.seal import mx__seal_cfdi
from mcp_cfdi_mx.utils.xml_builder import build_comprobante_xml


class TestSealCfdi:
    def test_pac_mode_returns_xml_unchanged(self, comprobante_ingreso: CFDIComprobante) -> None:
        xml = build_comprobante_xml(comprobante_ingreso).decode()
        result = mx__seal_cfdi(xml, sealing_mode="pac")
        assert result["xml"] == xml
        assert result["sealing_mode"] == "pac"

    def test_local_mode_populates_sello(
        self, comprobante_ingreso: CFDIComprobante, csd_paths
    ) -> None:
        cert_path, key_path = csd_paths
        xml = build_comprobante_xml(comprobante_ingreso).decode()
        result = mx__seal_cfdi(
            xml,
            sealing_mode="local",
            cert_path=cert_path,
            key_path=key_path,
            key_password="test",
            no_certificado="30001000000500003416",
        )
        assert "error" not in result
        root = etree.fromstring(result["xml"].encode())
        assert root.get("NoCertificado") == "30001000000500003416"
        assert root.get("Sello")
        assert root.get("Certificado")
        assert result["sealing_mode"] == "local"

    def test_local_mode_missing_arguments(self, comprobante_ingreso: CFDIComprobante) -> None:
        xml = build_comprobante_xml(comprobante_ingreso).decode()
        result = mx__seal_cfdi(xml, sealing_mode="local")
        assert result["error"] == "missing_arguments"
        assert "cert_path" in result["details"]

    def test_local_mode_wrong_password_reports_error(
        self, comprobante_ingreso: CFDIComprobante, csd_paths
    ) -> None:
        cert_path, key_path = csd_paths
        xml = build_comprobante_xml(comprobante_ingreso).decode()
        result = mx__seal_cfdi(
            xml,
            sealing_mode="local",
            cert_path=cert_path,
            key_path=key_path,
            key_password="wrong-password",
            no_certificado="30001000000500003416",
        )
        assert result["error"] == "sealing_error"
