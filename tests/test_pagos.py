"""Tests for mcp_cfdi_mx.models.pagos."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mcp_cfdi_mx.models import Pago, PagoDoctoRelacionado, Pagos20, Totales


@pytest.fixture()
def docto_relacionado() -> PagoDoctoRelacionado:
    return PagoDoctoRelacionado(
        id_documento="12345678-1234-1234-1234-123456789012",
        moneda_dr="MXN",
        num_parcialidad="1",
        imp_saldo_ant="100.00",
        imp_pagado="100.00",
        imp_saldo_insoluto="0.00",
        objeto_imp_dr="02",
    )


@pytest.fixture()
def pago(docto_relacionado: PagoDoctoRelacionado) -> Pago:
    return Pago(
        fecha_pago="2026-09-01T12:00:00",
        forma_de_pago_p="03",
        moneda_p="MXN",
        monto="100.00",
        doctos_relacionados=[docto_relacionado],
    )


@pytest.fixture()
def totales() -> Totales:
    return Totales(monto_total_pagos="100.00")


class TestPagos20:
    def test_builds_valid_pagos20(self, pago: Pago, totales: Totales) -> None:
        complemento = Pagos20(pagos=[pago], totales=totales)
        assert complemento.version == "2.0"
        assert len(complemento.pagos) == 1

    def test_requires_at_least_one_pago(self, totales: Totales) -> None:
        with pytest.raises(ValidationError):
            Pagos20(pagos=[], totales=totales)

    def test_totales_is_required(self, pago: Pago) -> None:
        with pytest.raises(ValidationError):
            Pagos20(pagos=[pago])  # type: ignore[call-arg]

    def test_pago_requires_at_least_one_docto_relacionado(self) -> None:
        with pytest.raises(ValidationError):
            Pago(
                fecha_pago="2026-09-01T12:00:00",
                forma_de_pago_p="03",
                moneda_p="MXN",
                monto="100.00",
                doctos_relacionados=[],
            )

    def test_version_is_frozen(self, pago: Pago, totales: Totales) -> None:
        complemento = Pagos20(pagos=[pago], totales=totales)
        with pytest.raises(ValidationError):
            complemento.version = "1.0"


class TestSaldoReconciliation:
    """MX-SC-4: ImpSaldoAnt must equal ImpPagado + ImpSaldoInsoluto."""

    def test_unbalanced_amounts_rejected(self) -> None:
        with pytest.raises(ValidationError, match="ImpSaldoAnt"):
            PagoDoctoRelacionado(
                id_documento="12345678-1234-1234-1234-123456789012",
                moneda_dr="MXN",
                num_parcialidad="1",
                imp_saldo_ant="100.00",
                imp_pagado="40.00",
                imp_saldo_insoluto="40.00",
                objeto_imp_dr="02",
            )

    def test_balanced_amounts_accepted(self) -> None:
        docto = PagoDoctoRelacionado(
            id_documento="12345678-1234-1234-1234-123456789012",
            moneda_dr="MXN",
            num_parcialidad="1",
            imp_saldo_ant="100.00",
            imp_pagado="40.00",
            imp_saldo_insoluto="60.00",
            objeto_imp_dr="02",
        )
        assert docto.imp_saldo_ant == "100.00"
