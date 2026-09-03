"""Mexican CFDI 4.0 models — extend mcp-einvoicing-core InvoiceDocument.

CFDI 4.0 predates and is structurally unrelated to EN 16931 (CEN TC 434) — it is a
clearance-model document certified by a PAC (Proveedor Autorizado de Certificación)
before it is legally valid. `mcp-cfdi-mx` therefore follows the non-EN16931 pathway:
`CFDIComprobante` extends `InvoiceDocument`, not `EN16931Invoice`. Same determination
as `mcp-nfe-br`'s `BRInvoice`.

Field-level structure and every namespace/format constraint cited here is traced to
the supplied SAT spec bundle under ``specs/`` — see
context-library/countries/mx.md (workspace root repo) for the verified reference,
including source citations for every value below.

Phase 1 scope only: CFDI 4.0 Ingreso + Egreso + Complemento de Pagos 2.0. Fields for
out-of-scope complementos (Carta Porte, Nómina, Comercio Exterior, Retenciones) are not
modeled — see mx.md "Known gaps and open items" and roadmap-2026.md.

Unlike ``mcp-nfe-br``'s ``BRInvoice`` (which adds parallel ``emitente``/``destinatario``
fields alongside the inherited, unused ``seller``/``buyer``), this model narrows
``seller``/``buyer`` to the MX-specific party types directly — no duplicate fields,
and the base class's required-ness is preserved rather than left as a latent gap.
"""

from __future__ import annotations

from enum import StrEnum

from mcp_einvoicing_core.models import InvoiceDocument, InvoiceLineItem, InvoiceParty, TaxIdentifier
from pydantic import BaseModel, Field, field_validator, model_validator

# `t_FechaH` restriction, verbatim from specs/tdCFDI.xsd:99 (AAAA-MM-DDThh:mm:ss).
_T_FECHAH_PATTERN = (
    r"(20[1-9][0-9])-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])"
    r"T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9])"
)

# `Nombre` attribute restriction, verbatim from specs/cfdv40.xsd.xml:82-92 (Emisor)
# and :124-135 (Receptor) — identical minLength=1/maxLength=300/pattern in both.
_T_NOMBRE_PATTERN = r"[^|]{1,300}"

# Generic ("público en general" / foreign-resident) RFCs and their required
# RegimenFiscalReceptor/UsoCFDI pairing. Both XAXX010101000 and XEXX010101000
# require RegimenFiscalReceptor="616" — confirmed in Anexo20_2022.pdf (DOF
# 2022-01-13), "RegimenFiscalReceptor" validation clause: "Si el atributo Rfc
# del nodo Receptor contiene el valor 'XAXX010101000' o el valor
# 'XEXX010101000' en este atributo se debe registrar la clave '616'." UsoCFDI
# must be "S01" for both on non-Pago CFDIs — confirmed in
# Anexo_20_Guia_de_llenado_CFDI.pdf (XEXX: "en este campo se debe registrar la
# clave 'S01'"; XAXX: worked example "Uso del CFDI: S01"). This does NOT apply
# to Pago-type CFDIs: Guia_llenado_pagos.pdf fixes UsoCFDI="CP01" for every
# Pago CFDI regardless of receptor RFC, with no generic-RFC exception.
_GENERIC_RFC_REGIMEN_FISCAL = "616"
_GENERIC_RFC_USO_CFDI = "S01"
_GENERIC_RFCS = frozenset({"XAXX010101000", "XEXX010101000"})


class TipoDeComprobante(StrEnum):
    """`c_TipoDeComprobante` (catCFDI.xsd). Phase 1 uses I, E, P only."""

    INGRESO = "I"
    EGRESO = "E"
    TRASLADO = "T"
    NOMINA = "N"
    PAGO = "P"


class MetodoPago(StrEnum):
    """`c_MetodoPago` (catCFDI_V_4_*.xls, sheet c_MetodoPago)."""

    PUE = "PUE"
    PPD = "PPD"


def _validate_rfc(v: str) -> str:
    rfc = v.strip().upper()
    ok, error = TaxIdentifier.validate_mx_rfc(rfc)
    if not ok:
        raise ValueError(f"Invalid RFC {v!r}: {error}")
    return rfc


class MXEmisor(InvoiceParty):
    """Emisor (Grupo `Emisor`).

    `tax_id.identifier` carries the RFC, validated via
    `TaxIdentifier.validate_mx_rfc` (core >=1.29.0) — format-only, see that
    method's docstring for why no check-digit is verified.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=300,
        pattern=_T_NOMBRE_PATTERN,
        description="Nombre, denominación o razón social del emisor (Nombre, cfdv40.xsd.xml:82-92)",
    )
    regimen_fiscal: str = Field(
        ..., description="Clave del régimen fiscal del emisor (catálogo c_RegimenFiscal)"
    )

    @field_validator("tax_id")
    @classmethod
    def _validate_emisor_rfc(cls, v: TaxIdentifier) -> TaxIdentifier:
        v.identifier = _validate_rfc(v.identifier)
        return v


class MXReceptor(InvoiceParty):
    """Receptor (Grupo `Receptor`).

    `domicilio_fiscal_receptor` is required by the schema
    (`cfdv40.xsd.xml`, `DomicilioFiscalReceptor`, `use="required"`) — the
    5-digit postal code of the receptor's registered fiscal address, not
    necessarily the delivery address.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=300,
        pattern=_T_NOMBRE_PATTERN,
        description=(
            "Nombre, denominación o razón social del receptor (Nombre, cfdv40.xsd.xml:124-135)"
        ),
    )
    regimen_fiscal_receptor: str = Field(
        ..., description="Clave del régimen fiscal del receptor (catálogo c_RegimenFiscal)"
    )
    uso_cfdi: str = Field(
        ...,
        description=(
            "Uso que el receptor dará al comprobante (catálogo c_UsoCFDI). "
            "'CP01' es obligatorio para un CFDI de Complemento de Pagos 2.0."
        ),
    )
    domicilio_fiscal_receptor: str = Field(
        ...,
        min_length=5,
        max_length=5,
        description="Código postal del domicilio fiscal (5 dígitos)",
    )

    @field_validator("tax_id")
    @classmethod
    def _validate_receptor_rfc(cls, v: TaxIdentifier) -> TaxIdentifier:
        v.identifier = _validate_rfc(v.identifier)
        return v


class ConceptoImpuesto(BaseModel):
    """One `Concepto/Impuestos/(Traslados/Traslado | Retenciones/Retencion)` entry.

    `impuesto`: `catCFDI:c_Impuesto` — `"001"`=ISR, `"002"`=IVA, `"003"`=IEPS
    (XSD-confirmed 3-digit zero-padded codes; do not use the bare `1`/`2`/`3`
    shown in the catálogos workbook's display column).
    `tipo_factor`: `catCFDI:c_TipoFactor` — `"Tasa"` \\| `"Cuota"` \\| `"Exento"`.
    `tasa_o_cuota`/`importe` are required when `tipo_factor` is `"Tasa"` or
    `"Cuota"`, and must be absent when `"Exento"` — enforced by the XML
    builder, not by this model (the model stays a plain data container).
    """

    base: str = Field(..., description="Base para el cálculo del impuesto")
    impuesto: str = Field(..., description="Clave del catálogo c_Impuesto")
    tipo_factor: str = Field(..., description="Clave del catálogo c_TipoFactor")
    tasa_o_cuota: str | None = Field(
        default=None, description="Requerido cuando TipoFactor es 'Tasa' o 'Cuota'"
    )
    importe: str | None = Field(
        default=None, description="Requerido cuando TipoFactor es 'Tasa' o 'Cuota'"
    )


class CFDIConcepto(InvoiceLineItem):
    """Concepto (line item), Grupo `Conceptos/Concepto`.

    `Conceptos/Concepto` has no `maxOccurs` cap in `cfdv40.xsd.xml` (line
    184) — unbounded.
    """

    clave_prod_serv: str = Field(
        ..., description="Clave del producto o servicio (catálogo c_ClaveProdServ)"
    )
    clave_unidad: str = Field(..., description="Clave de unidad (catálogo c_ClaveUnidad)")
    objeto_imp: str = Field(
        ...,
        description="Clave que expresa si el concepto es objeto de impuesto (catálogo c_ObjetoImp)",
    )
    traslados: list[ConceptoImpuesto] = Field(
        default_factory=list, description="Impuestos trasladados aplicables a este concepto"
    )
    retenciones: list[ConceptoImpuesto] = Field(
        default_factory=list, description="Impuestos retenidos aplicables a este concepto"
    )


class CfdiRelacionado(BaseModel):
    """One entry of Grupo `CfdiRelacionados` (used by Egreso to reference the Ingreso it credits)."""

    uuid: str = Field(..., min_length=36, max_length=36, description="UUID del CFDI relacionado")
    tipo_relacion: str = Field(
        ..., description="Clave del catálogo c_TipoRelacion (p.ej. '01' Nota de crédito)"
    )


class CFDIComprobante(InvoiceDocument):
    """CFDI 4.0 `Comprobante` root document.

    Extends `InvoiceDocument` with the attributes CFDI 4.0 requires that
    have no EN 16931 equivalent, per `cfdv40.xsd.xml`'s `Comprobante`
    attribute list. `seller`/`buyer` are narrowed to `MXEmisor`/`MXReceptor`
    rather than duplicated under native SAT names.

    Sealing (`Sello`/`NoCertificado`/`Certificado`) is populated by
    `mcp_einvoicing_core.digital_signature.SelloDigitalSigner`, not by this
    model — see the `sealing_mode` design in mx.md.
    """

    seller: MXEmisor
    buyer: MXReceptor
    lines: list[CFDIConcepto] = Field(default_factory=list, min_length=1)  # type: ignore[assignment]

    date: str = Field(
        ...,
        pattern=_T_FECHAH_PATTERN,
        description="Fecha y hora de expedición (t_FechaH, AAAA-MM-DDThh:mm:ss), tdCFDI.xsd:99",
    )

    currency: str = Field(default="MXN", min_length=3, max_length=3)

    version: str = Field(default="4.0", frozen=True, description="Atributo Version, fijo en '4.0'")
    serie: str | None = Field(default=None, description="Serie del comprobante")
    folio: str | None = Field(default=None, description="Folio del comprobante")
    tipo_de_comprobante: TipoDeComprobante = Field(
        ..., description="I=Ingreso, E=Egreso, P=Pago (Phase 1 scope)"
    )
    lugar_expedicion: str = Field(
        ..., min_length=5, max_length=5, description="Código postal del lugar de expedición"
    )
    sub_total: str = Field(
        ..., description="Suma de importes de conceptos antes de descuento e impuesto"
    )
    descuento: str | None = Field(default=None, description="Descuento aplicable")
    forma_pago: str | None = Field(
        default=None, description="Clave de la forma de pago (catálogo c_FormaPago)"
    )
    metodo_pago: MetodoPago | None = Field(default=None, description="PUE o PPD")
    condiciones_de_pago: str | None = Field(default=None, description="Condiciones de pago")
    tipo_cambio: str | None = Field(
        default=None,
        description="Requerido cuando Moneda distinto de MXN y XXX (catálogo c_Moneda)",
    )
    confirmacion: str | None = Field(
        default=None, description="Clave de confirmación otorgada por el PAC cuando aplica"
    )
    exportacion: str = Field(
        default="01", description="Clave del catálogo c_Exportacion (default '01' No aplica)"
    )

    # Populated by SelloDigitalSigner, not set directly by the caller.
    no_certificado: str | None = Field(default=None, min_length=20, max_length=20)
    certificado: str | None = None
    sello: str | None = None

    cfdi_relacionados: list[CfdiRelacionado] = Field(
        default_factory=list,
        description="Grupo CfdiRelacionados (usado por Egreso para referenciar el Ingreso que abona)",
    )

    @model_validator(mode="after")
    def _validate_generic_rfc_receptor(self) -> CFDIComprobante:
        if self.buyer.tax_id.identifier not in _GENERIC_RFCS:
            return self
        if self.buyer.regimen_fiscal_receptor != _GENERIC_RFC_REGIMEN_FISCAL:
            raise ValueError(
                f"Receptor RFC {self.buyer.tax_id.identifier!r} requires "
                f"regimen_fiscal_receptor={_GENERIC_RFC_REGIMEN_FISCAL!r} "
                "(Anexo 20, atributo RegimenFiscalReceptor)."
            )
        if (
            self.tipo_de_comprobante != TipoDeComprobante.PAGO
            and self.buyer.uso_cfdi != _GENERIC_RFC_USO_CFDI
        ):
            raise ValueError(
                f"Receptor RFC {self.buyer.tax_id.identifier!r} requires "
                f"uso_cfdi={_GENERIC_RFC_USO_CFDI!r} on non-Pago CFDIs "
                "(Guía de llenado del CFDI 4.0, atributo UsoCFDI)."
            )
        return self
