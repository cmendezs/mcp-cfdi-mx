"""Tests for mcp_cfdi_mx.models."""

from __future__ import annotations

import pytest
from mcp_einvoicing_core.models import TaxIdentifier
from pydantic import ValidationError

from mcp_cfdi_mx.models import (
    CFDIComprobante,
    CfdiRelacionado,
    MXEmisor,
    MXReceptor,
    TipoDeComprobante,
)


class TestCFDIComprobante:
    def test_builds_valid_ingreso(self, comprobante_ingreso: CFDIComprobante) -> None:
        assert comprobante_ingreso.currency == "MXN"
        assert comprobante_ingreso.version == "4.0"
        assert comprobante_ingreso.tipo_de_comprobante == TipoDeComprobante.INGRESO

    def test_is_invoice_document_subclass(self) -> None:
        from mcp_einvoicing_core.models import InvoiceDocument

        assert issubclass(CFDIComprobante, InvoiceDocument)

    def test_version_is_frozen(self, comprobante_ingreso: CFDIComprobante) -> None:
        with pytest.raises(ValidationError):
            comprobante_ingreso.version = "3.3"

    def test_egreso_with_cfdi_relacionados(
        self, emisor: MXEmisor, receptor: MXReceptor, concepto
    ) -> None:
        doc = CFDIComprobante(
            document_type="E",
            date="2026-09-01",
            number="NC-1",
            seller=emisor,
            buyer=receptor,
            lines=[concepto],
            tipo_de_comprobante=TipoDeComprobante.EGRESO,
            lugar_expedicion="06600",
            sub_total="100.00",
            cfdi_relacionados=[
                CfdiRelacionado(uuid="12345678-1234-1234-1234-123456789012", tipo_relacion="01")
            ],
        )
        assert len(doc.cfdi_relacionados) == 1
        assert doc.cfdi_relacionados[0].tipo_relacion == "01"

    def test_lines_require_at_least_one(self, emisor: MXEmisor, receptor: MXReceptor) -> None:
        with pytest.raises(ValidationError):
            CFDIComprobante(
                document_type="I",
                date="2026-09-01",
                number="A-1",
                seller=emisor,
                buyer=receptor,
                lines=[],
                tipo_de_comprobante=TipoDeComprobante.INGRESO,
                lugar_expedicion="06600",
                sub_total="0.00",
            )


class TestMXEmisorReceptorRfc:
    def test_valid_rfc_moral_accepted(self) -> None:
        emisor = MXEmisor(
            tax_id=TaxIdentifier(country_code="MX", identifier="aaa010101aa1"),
            name="X",
            regimen_fiscal="601",
        )
        assert emisor.tax_id.identifier == "AAA010101AA1"  # normalized upper

    def test_invalid_rfc_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Invalid RFC"):
            MXEmisor(
                tax_id=TaxIdentifier(country_code="MX", identifier="not-an-rfc"),
                name="X",
                regimen_fiscal="601",
            )

    def test_receptor_generic_publico_en_general_rfc(self) -> None:
        receptor = MXReceptor(
            tax_id=TaxIdentifier(country_code="MX", identifier="XAXX010101000"),
            name="Publico en General",
            regimen_fiscal_receptor="616",
            uso_cfdi="S01",
            domicilio_fiscal_receptor="06600",
        )
        assert receptor.tax_id.identifier == "XAXX010101000"

    def test_receptor_requires_domicilio_fiscal(self) -> None:
        with pytest.raises(ValidationError):
            MXReceptor(
                tax_id=TaxIdentifier(country_code="MX", identifier="XAXX010101000"),
                name="X",
                regimen_fiscal_receptor="616",
                uso_cfdi="S01",
            )
