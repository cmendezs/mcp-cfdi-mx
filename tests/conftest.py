"""Shared pytest fixtures for mcp-cfdi-mx tests."""

from __future__ import annotations

import pytest
from mcp_einvoicing_core.models import TaxIdentifier

from mcp_cfdi_mx.models import (
    CFDIComprobante,
    CFDIConcepto,
    MXEmisor,
    MXReceptor,
    TipoDeComprobante,
)


@pytest.fixture()
def emisor() -> MXEmisor:
    return MXEmisor(
        tax_id=TaxIdentifier(country_code="MX", identifier="AAA010101AA1"),
        name="Emisor de Prueba SA de CV",
        regimen_fiscal="601",
    )


@pytest.fixture()
def receptor() -> MXReceptor:
    return MXReceptor(
        tax_id=TaxIdentifier(country_code="MX", identifier="XAXX010101000"),
        name="Publico en General",
        regimen_fiscal_receptor="616",
        uso_cfdi="S01",
        domicilio_fiscal_receptor="06600",
    )


@pytest.fixture()
def concepto() -> CFDIConcepto:
    return CFDIConcepto(
        line_number=1,
        description="Servicio de prueba",
        quantity=1,
        unit_price=100,
        total_price=100,
        vat_rate=16,
        currency="MXN",
        clave_prod_serv="84111506",
        clave_unidad="E48",
        objeto_imp="02",
    )


@pytest.fixture()
def comprobante_ingreso(
    emisor: MXEmisor, receptor: MXReceptor, concepto: CFDIConcepto
) -> CFDIComprobante:
    return CFDIComprobante(
        document_type="I",
        date="2026-09-01",
        number="A-1",
        seller=emisor,
        buyer=receptor,
        lines=[concepto],
        tipo_de_comprobante=TipoDeComprobante.INGRESO,
        lugar_expedicion="06600",
        sub_total="100.00",
    )
