"""Tests for mcp_cfdi_mx.models.pagos."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mcp_cfdi_mx.models import Pago, PagoDoctoRelacionado, Pagos20


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


class TestPagos20:
    def test_builds_valid_pagos20(self, pago: Pago) -> None:
        complemento = Pagos20(pagos=[pago])
        assert complemento.version == "2.0"
        assert len(complemento.pagos) == 1

    def test_requires_at_least_one_pago(self) -> None:
        with pytest.raises(ValidationError):
            Pagos20(pagos=[])

    def test_pago_requires_at_least_one_docto_relacionado(self) -> None:
        with pytest.raises(ValidationError):
            Pago(
                fecha_pago="2026-09-01T12:00:00",
                forma_de_pago_p="03",
                moneda_p="MXN",
                monto="100.00",
                doctos_relacionados=[],
            )

    def test_version_is_frozen(self, pago: Pago) -> None:
        complemento = Pagos20(pagos=[pago])
        with pytest.raises(ValidationError):
            complemento.version = "1.0"
