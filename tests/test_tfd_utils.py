"""Tests for mcp_cfdi_mx.utils.tfd."""

from __future__ import annotations

from lxml import etree

from mcp_cfdi_mx.utils.tfd import _TFD_NS, find_tfd, tfd_cadena_original, tfd_fields


def _sample_document_with_tfd() -> bytes:
    root = etree.Element("Comprobante")
    complemento = etree.SubElement(root, "Complemento")
    tfd_el = etree.SubElement(
        complemento, f"{{{_TFD_NS}}}TimbreFiscalDigital", nsmap={"tfd": _TFD_NS}
    )
    tfd_el.set("Version", "1.1")
    tfd_el.set("UUID", "12345678-1234-1234-1234-123456789012")
    tfd_el.set("FechaTimbrado", "2026-09-01T12:05:00")
    tfd_el.set("RfcProvCertif", "PPC010101AA1")
    tfd_el.set("SelloCFD", "abc123")
    tfd_el.set("NoCertificadoSAT", "30001000000500003417")
    tfd_el.set("SelloSAT", "def456")
    return etree.tostring(root)


class TestFindTfd:
    def test_finds_nested_tfd(self) -> None:
        tfd_el = find_tfd(_sample_document_with_tfd())
        assert tfd_el is not None
        assert tfd_el.get("UUID") == "12345678-1234-1234-1234-123456789012"

    def test_returns_none_when_absent(self) -> None:
        assert find_tfd(b"<Comprobante/>") is None


class TestTfdFields:
    def test_returns_all_known_attributes(self) -> None:
        tfd_el = find_tfd(_sample_document_with_tfd())
        fields = tfd_fields(tfd_el)
        assert fields["UUID"] == "12345678-1234-1234-1234-123456789012"
        assert fields["Leyenda"] is None


class TestCadenaOriginal:
    def test_deterministic_and_pipe_delimited(self) -> None:
        tfd_el = find_tfd(_sample_document_with_tfd())
        cadena = tfd_cadena_original(tfd_el)
        text = cadena.decode()
        assert text.startswith("|")
        assert text.endswith("||")
        assert "1.1" in text
        assert "12345678-1234-1234-1234-123456789012" in text

    def test_changes_when_attribute_changes(self) -> None:
        tfd_el = find_tfd(_sample_document_with_tfd())
        original = tfd_cadena_original(tfd_el)
        tfd_el.set("FechaTimbrado", "2026-09-01T12:05:01")
        changed = tfd_cadena_original(tfd_el)
        assert original != changed
