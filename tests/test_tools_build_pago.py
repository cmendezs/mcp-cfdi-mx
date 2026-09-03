"""Tests for mcp_cfdi_mx.tools.build_pago (mx__build_pago)."""

from __future__ import annotations

from lxml import etree

from mcp_cfdi_mx.tools.build_pago import mx__build_pago
from mcp_cfdi_mx.utils.xml_builder import CFDI_NS


def _q(local: str) -> str:
    return f"{{{CFDI_NS}}}{local}"


def _comprobante_data() -> dict:
    return {
        "document_type": "P",
        "date": "2026-09-01T12:00:00",
        "number": "P-1",
        "seller": {
            "tax_id": {"country_code": "MX", "identifier": "AAA010101AA1"},
            "name": "Emisor SA",
            "regimen_fiscal": "601",
        },
        "buyer": {
            "tax_id": {"country_code": "MX", "identifier": "XAXX010101000"},
            "name": "Cliente",
            "regimen_fiscal_receptor": "616",
            "uso_cfdi": "CP01",
            "domicilio_fiscal_receptor": "06600",
        },
        "lugar_expedicion": "06600",
    }


def _pagos_data() -> dict:
    return {
        "totales": {"monto_total_pagos": "100.00"},
        "pagos": [
            {
                "fecha_pago": "2026-09-01T12:00:00",
                "forma_de_pago_p": "03",
                "moneda_p": "MXN",
                "monto": "100.00",
                "doctos_relacionados": [
                    {
                        "id_documento": "12345678-1234-1234-1234-123456789012",
                        "moneda_dr": "MXN",
                        "num_parcialidad": "1",
                        "imp_saldo_ant": "100.00",
                        "imp_pagado": "100.00",
                        "imp_saldo_insoluto": "0.00",
                        "objeto_imp_dr": "02",
                    }
                ],
            }
        ],
    }


class TestBuildPago:
    def test_returns_xml(self) -> None:
        result = mx__build_pago(_comprobante_data(), _pagos_data())
        assert "error" not in result
        root = etree.fromstring(result["xml"].encode())
        assert root.get("TipoDeComprobante") == "P"

    def test_fixed_concepto_values(self) -> None:
        result = mx__build_pago(_comprobante_data(), _pagos_data())
        root = etree.fromstring(result["xml"].encode())
        concepto = root.find(f"{_q('Conceptos')}/{_q('Concepto')}")
        assert concepto.get("ClaveProdServ") == "84111506"
        assert concepto.get("ClaveUnidad") == "ACT"
        assert concepto.get("Descripcion") == "Pago"
        assert concepto.get("ValorUnitario") == "0"
        assert concepto.get("Importe") == "0"
        assert concepto.get("ObjetoImp") == "01"
        assert concepto.get("Unidad") is None
        assert concepto.find(_q("Impuestos")) is None

    def test_fixed_comprobante_values(self) -> None:
        result = mx__build_pago(_comprobante_data(), _pagos_data())
        root = etree.fromstring(result["xml"].encode())
        assert root.get("SubTotal") == "0"
        assert root.get("Total") == "0"
        assert root.get("Moneda") == "XXX"
        assert root.get("FormaPago") is None
        assert root.get("MetodoPago") is None
        assert root.get("CondicionesDePago") is None

    def test_pagos_complement_attached(self) -> None:
        result = mx__build_pago(_comprobante_data(), _pagos_data())
        root = etree.fromstring(result["xml"].encode())
        complemento = root.find(_q("Complemento"))
        assert complemento is not None
        pagos_el = complemento.find("{http://www.sat.gob.mx/Pagos20}Pagos")
        assert pagos_el is not None
        assert pagos_el.get("Version") == "2.0"

    def test_invalid_pagos_data_returns_validation_error(self) -> None:
        bad_pagos = _pagos_data()
        del bad_pagos["pagos"]
        result = mx__build_pago(_comprobante_data(), bad_pagos)
        assert result["error"] == "validation_error"
        assert result["field"] == "pagos_data"

    def test_invalid_comprobante_data_returns_validation_error(self) -> None:
        bad_comprobante = _comprobante_data()
        del bad_comprobante["lugar_expedicion"]
        result = mx__build_pago(bad_comprobante, _pagos_data())
        assert result["error"] == "validation_error"
        assert result["field"] == "comprobante_data"

    def test_uso_cfdi_forced_to_cp01(self) -> None:
        mismatched = _comprobante_data()
        mismatched["buyer"]["uso_cfdi"] = "G03"
        result = mx__build_pago(mismatched, _pagos_data())
        assert "error" not in result
        root = etree.fromstring(result["xml"].encode())
        receptor_el = root.find(_q("Receptor"))
        assert receptor_el.get("UsoCFDI") == "CP01"
