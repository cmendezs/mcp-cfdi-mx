"""Complemento de Pagos 2.0 models (`Pagos20.xsd.xml`, namespace ``http://www.sat.gob.mx/Pagos20``).

Phase 1 scope. Field names and cardinality traced directly to the supplied
``Pagos20.xsd.xml`` — see context-library/countries/mx.md (workspace root repo).
This complement attaches to a `CFDIComprobante` with
`tipo_de_comprobante=TipoDeComprobante.PAGO` via
`CFDIComprobante`'s `Complemento` node — not modeled as a Pydantic field on
`CFDIComprobante` itself, since a complemento is schema-attached XML, not an
EN 16931/InvoiceDocument-shaped concept. The generator tool composes the two.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ImpuestoDR(BaseModel):
    """One entry of `Pago/DoctoRelacionado/ImpuestosDR/(TrasladosDR|RetencionesDR)`."""

    base_dr: str = Field(..., description="BaseDR — base del impuesto")
    impuesto_dr: str = Field(..., description="ImpuestoDR — clave del catálogo c_Impuesto")
    tipo_factor_dr: str = Field(..., description="TipoFactorDR — clave del catálogo c_TipoFactor")
    tasa_o_cuota_dr: str | None = Field(
        default=None, description="TasaOCuotaDR — requerido salvo TipoFactorDR='Exento'"
    )
    importe_dr: str | None = Field(
        default=None, description="ImporteDR — requerido salvo TipoFactorDR='Exento'"
    )


class PagoDoctoRelacionado(BaseModel):
    """`Pago/DoctoRelacionado` — one prior CFDI (Ingreso, PPD) being paid down."""

    id_documento: str = Field(
        ..., min_length=36, max_length=36, description="UUID del CFDI de Ingreso"
    )
    serie: str | None = None
    folio: str | None = None
    moneda_dr: str = Field(..., description="MonedaDR — clave del catálogo c_Moneda")
    equivalencia_dr: str | None = Field(
        default=None, description="Requerido si MonedaDR es distinta de la moneda del pago"
    )
    num_parcialidad: str = Field(..., description="Número de parcialidad que se está pagando")
    imp_saldo_ant: str = Field(..., description="Importe del saldo insoluto anterior")
    imp_pagado: str = Field(..., description="Importe pagado para este documento")
    imp_saldo_insoluto: str = Field(..., description="Importe del saldo insoluto restante")
    objeto_imp_dr: str = Field(..., description="ObjetoImpDR — clave del catálogo c_ObjetoImp")
    traslados_dr: list[ImpuestoDR] = Field(default_factory=list)
    retenciones_dr: list[ImpuestoDR] = Field(default_factory=list)


class Pago(BaseModel):
    """`Pago` — one payment event, possibly covering several `DoctoRelacionado` entries."""

    fecha_pago: str = Field(..., description="Fecha y hora del pago (ISO 8601)")
    forma_de_pago_p: str = Field(..., description="FormaDePagoP — clave del catálogo c_FormaPago")
    moneda_p: str = Field(..., description="MonedaP — clave del catálogo c_Moneda")
    tipo_cambio_p: str | None = Field(
        default=None, description="Requerido si MonedaP es distinta de MXN"
    )
    monto: str = Field(..., description="Monto del pago")
    num_operacion: str | None = None
    rfc_emisor_cta_ord: str | None = Field(
        default=None,
        description="RFC del emisor de la cuenta ordenante, si es una entidad financiera nacional",
    )
    cta_ordenante: str | None = None
    rfc_emisor_cta_ben: str | None = Field(
        default=None,
        description="RFC del emisor de la cuenta beneficiaria (siempre persona moral, t_RFC_PM)",
    )
    cta_beneficiario: str | None = None
    doctos_relacionados: list[PagoDoctoRelacionado] = Field(..., min_length=1)


class Totales(BaseModel):
    """`Pagos/Totales` — optional aggregate totals across all `Pago` entries."""

    total_retenciones_iva: str | None = None
    total_retenciones_isr: str | None = None
    total_retenciones_ieps: str | None = None
    total_traslados_base_iva16: str | None = None
    total_traslados_impuesto_iva16: str | None = None
    total_traslados_base_iva8: str | None = None
    total_traslados_impuesto_iva8: str | None = None
    total_traslados_base_iva0: str | None = None
    total_traslados_impuesto_iva0: str | None = None
    total_traslados_base_iva_exento: str | None = None
    monto_total_pagos: str = Field(..., description="MontoTotalPagos — suma de todos los pagos")


class Pagos20(BaseModel):
    """`Pagos` root complement element. `Version` fixed at `2.0`."""

    version: str = Field(default="2.0", frozen=True)
    totales: Totales | None = None
    pagos: list[Pago] = Field(..., min_length=1)
