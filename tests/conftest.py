"""Shared pytest fixtures for mcp-cfdi-mx tests."""

from __future__ import annotations

import datetime
import os

import pytest
from mcp_einvoicing_core.models import TaxIdentifier

from mcp_cfdi_mx.models import (
    CFDIComprobante,
    CFDIConcepto,
    ConceptoImpuesto,
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
def concepto_con_iva() -> CFDIConcepto:
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
        traslados=[
            ConceptoImpuesto(
                base="100.00",
                impuesto="002",
                tipo_factor="Tasa",
                tasa_o_cuota="0.160000",
                importe="16.00",
            )
        ],
    )


@pytest.fixture()
def comprobante_ingreso(
    emisor: MXEmisor, receptor: MXReceptor, concepto: CFDIConcepto
) -> CFDIComprobante:
    return CFDIComprobante(
        document_type="I",
        date="2026-09-01T12:00:00",
        number="A-1",
        seller=emisor,
        buyer=receptor,
        lines=[concepto],
        tipo_de_comprobante=TipoDeComprobante.INGRESO,
        lugar_expedicion="06600",
        sub_total="100.00",
    )


@pytest.fixture()
def comprobante_con_iva(
    emisor: MXEmisor, receptor: MXReceptor, concepto_con_iva: CFDIConcepto
) -> CFDIComprobante:
    return CFDIComprobante(
        document_type="I",
        date="2026-09-01T12:00:00",
        number="A-1",
        seller=emisor,
        buyer=receptor,
        lines=[concepto_con_iva],
        tipo_de_comprobante=TipoDeComprobante.INGRESO,
        lugar_expedicion="06600",
        sub_total="100.00",
    )


def _generate_test_csd(cert_path: str, key_path: str, password: bytes = b"test") -> None:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test CSD")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    with open(cert_path, "wb") as fh:
        fh.write(cert.public_bytes(serialization.Encoding.DER))
    with open(key_path, "wb") as fh:
        fh.write(
            key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(password),
            )
        )


@pytest.fixture()
def csd_paths(tmp_path) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    cert_path = os.path.join(tmp_path, "csd.cer")
    key_path = os.path.join(tmp_path, "csd.key")
    _generate_test_csd(cert_path, key_path, password=b"test")
    return cert_path, key_path
