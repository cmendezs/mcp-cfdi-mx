"""Tests for mcp_cfdi_mx.tools.verify_tfd (mx__verify_tfd)."""

from __future__ import annotations

import base64
import datetime

import pytest
from lxml import etree

from mcp_cfdi_mx.tools.verify_tfd import mx__verify_tfd
from mcp_cfdi_mx.utils.tfd import _TFD_NS, tfd_cadena_original


def _generate_pac_key_and_cert():  # type: ignore[no-untyped-def]
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test PAC")])
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
    return key, cert.public_bytes(serialization.Encoding.DER)


@pytest.fixture()
def stamped_document() -> tuple[str, str]:
    """Return (xml_with_tfd, pac_cert_der_b64)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    pac_key, pac_cert_der = _generate_pac_key_and_cert()

    root = etree.Element("Comprobante")
    complemento = etree.SubElement(root, "Complemento")
    tfd_el = etree.SubElement(
        complemento, f"{{{_TFD_NS}}}TimbreFiscalDigital", nsmap={"tfd": _TFD_NS}
    )
    tfd_el.set("Version", "1.1")
    tfd_el.set("UUID", "12345678-1234-1234-1234-123456789012")
    tfd_el.set("FechaTimbrado", "2026-09-01T12:05:00")
    tfd_el.set("RfcProvCertif", "PPC010101AA1")
    tfd_el.set("SelloCFD", "dummy-emisor-sello")
    tfd_el.set("NoCertificadoSAT", "30001000000500003417")

    cadena = tfd_cadena_original(tfd_el)
    signature = pac_key.sign(cadena, padding.PKCS1v15(), hashes.SHA256())
    tfd_el.set("SelloSAT", base64.b64encode(signature).decode())

    xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8").decode()
    return xml, base64.b64encode(pac_cert_der).decode()


class TestVerifyTfd:
    def test_no_tfd_present(self) -> None:
        result = mx__verify_tfd("<Comprobante/>")
        assert result["found"] is False

    def test_parses_fields_without_cert(self, stamped_document: tuple[str, str]) -> None:
        xml, _ = stamped_document
        result = mx__verify_tfd(xml)
        assert result["found"] is True
        assert result["fields"]["UUID"] == "12345678-1234-1234-1234-123456789012"
        assert result["sello_sat_verified"] is None

    def test_verifies_valid_signature(self, stamped_document: tuple[str, str]) -> None:
        xml, pac_cert_b64 = stamped_document
        result = mx__verify_tfd(xml, pac_certificado_der_b64=pac_cert_b64)
        assert result["sello_sat_verified"] is True

    def test_rejects_tampered_document(self, stamped_document: tuple[str, str]) -> None:
        xml, pac_cert_b64 = stamped_document
        tampered = xml.replace(
            'FechaTimbrado="2026-09-01T12:05:00"', 'FechaTimbrado="2026-09-01T12:05:01"'
        )
        result = mx__verify_tfd(tampered, pac_certificado_der_b64=pac_cert_b64)
        assert result["sello_sat_verified"] is False

    def test_rejects_wrong_cert(self, stamped_document: tuple[str, str]) -> None:
        xml, _ = stamped_document
        _, other_cert_der = _generate_pac_key_and_cert()
        result = mx__verify_tfd(
            xml, pac_certificado_der_b64=base64.b64encode(other_cert_der).decode()
        )
        assert result["sello_sat_verified"] is False

    def test_malformed_xml(self) -> None:
        result = mx__verify_tfd("<not valid")
        assert result["found"] is False
        assert result["error"] == "xml_parse_error"
