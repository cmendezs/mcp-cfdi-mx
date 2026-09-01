"""Tests for mcp_cfdi_mx.utils.xsd_validator."""

from __future__ import annotations

from mcp_cfdi_mx.models.invoice import CFDIComprobante
from mcp_cfdi_mx.utils.xml_builder import build_comprobante_xml
from mcp_cfdi_mx.utils.xsd_validator import (
    cfdi_validator,
    full_validator,
    pagos_validator,
    tfd_validator,
)


class TestValidators:
    def test_cfdi_validator_rejects_malformed_xml(self) -> None:
        result = cfdi_validator().validate(b"<not valid xml", profile="cfdi40")
        assert result.is_valid is False
        assert result.errors[0].rule_id == "XML-PARSE"

    def test_cfdi_validator_flags_missing_required_element(self) -> None:
        result = cfdi_validator().validate(b"<Comprobante/>", profile="cfdi40")
        assert result.is_valid is False

    def test_full_validator_without_complements_behaves_like_cfdi_validator(
        self, comprobante_ingreso: CFDIComprobante
    ) -> None:
        xml = build_comprobante_xml(comprobante_ingreso)
        plain = cfdi_validator().validate(xml, profile="cfdi40")
        combined = full_validator().validate(xml, profile="cfdi40")
        assert {e.text for e in plain.errors} == {e.text for e in combined.errors}

    def test_tfd_validator_rejects_missing_document(self) -> None:
        result = tfd_validator().validate(b"<TimbreFiscalDigital/>", profile="tfd11")
        assert result.is_valid is False

    def test_pagos_validator_rejects_missing_document(self) -> None:
        result = pagos_validator().validate(b"<Pagos/>", profile="pagos20")
        assert result.is_valid is False
