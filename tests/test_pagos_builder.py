"""Tests for mcp_cfdi_mx.utils.pagos_builder."""

from __future__ import annotations

from lxml import etree

from mcp_cfdi_mx.models.pagos import ImpuestoDR, Pago, PagoDoctoRelacionado, Pagos20, Totales
from mcp_cfdi_mx.utils.pagos_builder import PAGO20_NS, build_pagos_xml
from mcp_cfdi_mx.utils.xsd_validator import pagos_validator


def _q(local: str) -> str:
    return f"{{{PAGO20_NS}}}{local}"


def _docto(**overrides: str) -> PagoDoctoRelacionado:
    base = {
        "id_documento": "12345678-1234-1234-1234-123456789012",
        "moneda_dr": "MXN",
        "num_parcialidad": "1",
        "imp_saldo_ant": "100.00",
        "imp_pagado": "100.00",
        "imp_saldo_insoluto": "0.00",
        "objeto_imp_dr": "02",
    }
    base.update(overrides)
    return PagoDoctoRelacionado(**base)


class TestBuildPagos:
    def test_valid_pagos_xml(self) -> None:
        pago = Pago(
            fecha_pago="2026-09-01T12:00:00",
            forma_de_pago_p="03",
            moneda_p="MXN",
            monto="100.00",
            doctos_relacionados=[_docto()],
        )
        pagos = Pagos20(pagos=[pago], totales=Totales(monto_total_pagos="100.00"))
        xml = build_pagos_xml(pagos)
        result = pagos_validator().validate(xml, profile="pagos20")
        assert result.is_valid is True, result.errors

    def test_root_and_version(self) -> None:
        pago = Pago(
            fecha_pago="2026-09-01T12:00:00",
            forma_de_pago_p="03",
            moneda_p="MXN",
            monto="100.00",
            doctos_relacionados=[_docto()],
        )
        pagos = Pagos20(pagos=[pago], totales=Totales(monto_total_pagos="100.00"))
        root = etree.fromstring(build_pagos_xml(pagos))
        assert root.tag == _q("Pagos")
        assert root.get("Version") == "2.0"

    def test_docto_relacionado_with_traslado(self) -> None:
        docto = _docto(
            traslados_dr=[
                ImpuestoDR(
                    base_dr="100.00",
                    impuesto_dr="002",
                    tipo_factor_dr="Tasa",
                    tasa_o_cuota_dr="0.160000",
                    importe_dr="16.00",
                )
            ]
        )
        pago = Pago(
            fecha_pago="2026-09-01T12:00:00",
            forma_de_pago_p="03",
            moneda_p="MXN",
            monto="116.00",
            doctos_relacionados=[docto],
        )
        pagos = Pagos20(pagos=[pago], totales=Totales(monto_total_pagos="116.00"))
        xml = build_pagos_xml(pagos)
        result = pagos_validator().validate(xml, profile="pagos20")
        assert result.is_valid is True, result.errors
        root = etree.fromstring(xml)
        traslado_el = root.find(
            f"{_q('Pago')}/{_q('DoctoRelacionado')}/{_q('ImpuestosDR')}/{_q('TrasladosDR')}/{_q('TrasladoDR')}"
        )
        assert traslado_el.get("ImpuestoDR") == "002"

    def test_totales_always_emitted(self) -> None:
        pago = Pago(
            fecha_pago="2026-09-01T12:00:00",
            forma_de_pago_p="03",
            moneda_p="MXN",
            monto="100.00",
            doctos_relacionados=[_docto()],
        )
        pagos = Pagos20(pagos=[pago], totales=Totales(monto_total_pagos="100.00"))
        root = etree.fromstring(build_pagos_xml(pagos))
        totales_el = root.find(_q("Totales"))
        assert totales_el is not None
        assert totales_el.get("MontoTotalPagos") == "100.00"
