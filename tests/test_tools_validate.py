"""Tests for mcp_cfdi_mx.tools.validate (mx__validate_cfdi)."""

from __future__ import annotations

from mcp_cfdi_mx.models.invoice import CFDIComprobante
from mcp_cfdi_mx.tools.validate import mx__validate_cfdi
from mcp_cfdi_mx.utils.xml_builder import build_comprobante_xml


class TestValidateCfdi:
    def test_unsealed_ingreso_missing_sello_only(
        self, comprobante_ingreso: CFDIComprobante
    ) -> None:
        xml = build_comprobante_xml(comprobante_ingreso).decode()
        result = mx__validate_cfdi(xml)
        assert result["valid"] is False
        error_texts = " ".join(e["text"] for e in result["comprobante"]["errors"])
        assert "Sello" in error_texts
        assert "NoCertificado" in error_texts
        assert "Certificado" in error_texts

    def test_malformed_xml_reports_parse_error(self) -> None:
        result = mx__validate_cfdi("<not valid xml")
        assert result["valid"] is False
        assert result["error"] == "xml_parse_error"

    def test_no_tfd_or_pagos_keys_when_absent(self, comprobante_ingreso: CFDIComprobante) -> None:
        xml = build_comprobante_xml(comprobante_ingreso).decode()
        result = mx__validate_cfdi(xml)
        assert "tfd" not in result
        assert "pagos" not in result

    def test_sealed_document_is_valid(
        self, comprobante_ingreso: CFDIComprobante, csd_paths
    ) -> None:
        from mcp_cfdi_mx.tools.seal import mx__seal_cfdi

        cert_path, key_path = csd_paths
        unsealed = build_comprobante_xml(comprobante_ingreso).decode()
        sealed = mx__seal_cfdi(
            unsealed,
            sealing_mode="local",
            cert_path=cert_path,
            key_path=key_path,
            key_password="test",
            no_certificado="30001000000500003416",
        )
        result = mx__validate_cfdi(sealed["xml"])
        assert result["valid"] is True, result["comprobante"]["errors"]
