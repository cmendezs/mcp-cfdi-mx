"""Tests for mcp_cfdi_mx.tools.build (mx__build_cfdi)."""

from __future__ import annotations

from lxml import etree

from mcp_cfdi_mx.tools.build import mx__build_cfdi


def _comprobante_data(**overrides: object) -> dict:
    data = {
        "document_type": "I",
        "date": "2026-09-01T12:00:00",
        "number": "A-1",
        "seller": {
            "tax_id": {"country_code": "MX", "identifier": "AAA010101AA1"},
            "name": "Emisor SA",
            "regimen_fiscal": "601",
        },
        "buyer": {
            "tax_id": {"country_code": "MX", "identifier": "XAXX010101000"},
            "name": "Cliente",
            "regimen_fiscal_receptor": "616",
            "uso_cfdi": "S01",
            "domicilio_fiscal_receptor": "06600",
        },
        "lugar_expedicion": "06600",
        "sub_total": "100.00",
        "tipo_de_comprobante": "I",
        "lines": [
            {
                "line_number": 1,
                "description": "Servicio",
                "quantity": 1,
                "unit_price": 100,
                "total_price": 100,
                "vat_rate": 16,
                "currency": "MXN",
                "clave_prod_serv": "84111506",
                "clave_unidad": "E48",
                "objeto_imp": "02",
            }
        ],
    }
    data.update(overrides)
    return data


class TestBuildCfdi:
    def test_returns_xml(self) -> None:
        result = mx__build_cfdi(_comprobante_data())
        assert "error" not in result
        assert "<cfdi:Comprobante" in result["xml"]

    def test_total_returned(self) -> None:
        result = mx__build_cfdi(_comprobante_data())
        assert result["total"] == "100.00"

    def test_invalid_rfc_returns_validation_error(self) -> None:
        data = _comprobante_data()
        data["seller"]["tax_id"]["identifier"] = "NOT-AN-RFC"
        result = mx__build_cfdi(data)
        assert result["error"] == "validation_error"

    def test_pago_type_rejected(self) -> None:
        result = mx__build_cfdi(_comprobante_data(tipo_de_comprobante="P"))
        assert result["error"] == "wrong_tool"

    def test_egreso_builds(self) -> None:
        data = _comprobante_data(
            tipo_de_comprobante="E",
            cfdi_relacionados=[
                {"uuid": "12345678-1234-1234-1234-123456789012", "tipo_relacion": "01"}
            ],
        )
        result = mx__build_cfdi(data)
        assert "error" not in result
        root = etree.fromstring(result["xml"].encode())
        assert root.get("TipoDeComprobante") == "E"
