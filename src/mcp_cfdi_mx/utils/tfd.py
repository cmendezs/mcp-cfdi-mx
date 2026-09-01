"""Timbre Fiscal Digital 1.1 parsing and cadena original computation.

Distinct from `mcp_einvoicing_core.digital_signature.SelloDigitalSigner`:
that class computes and verifies the **emisor's own** `Sello` (attribute
names `Sello`/`NoCertificado`/`Certificado` on `Comprobante`, hardcoded).
The TFD is stamped by the PAC, using different attribute names
(`SelloSAT`/`NoCertificadoSAT`) and no embedded certificate — SAT does not
publish the PAC's public certificate inside the TFD itself, so verifying
`SelloSAT` cryptographically requires the caller to supply that
certificate's DER bytes separately. `SelloDigitalSigner`'s `verify()` cannot
be reused as-is for this: its attribute names are fixed to the emisor's
seal, not the PAC's. This module handles TFD's own cadena original
(`cadenaoriginal_TFD_1_1.xslt`, self-contained — no `xsl:include`s, unlike
the CFDI transform) directly with `lxml`, matching the same SHA-256 +
RSA-PKCS#1v1.5 algorithm confirmed in Anexo 20 (Rubro III.B extends the same
"Generación de sellos digitales" algorithm to the TFD).
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree
from mcp_einvoicing_core.xml_utils import safe_fromstring

_SPECS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "specs"
_TFD_CADENA_ORIGINAL_XSLT = _SPECS_DIR / "cadenaoriginal_TFD_1_1.xslt"

_TFD_NS = "http://www.sat.gob.mx/TimbreFiscalDigital"

_TFD_ATTRS = (
    "Version",
    "UUID",
    "FechaTimbrado",
    "RfcProvCertif",
    "Leyenda",
    "SelloCFD",
    "NoCertificadoSAT",
    "SelloSAT",
)


def find_tfd(document: bytes) -> etree._Element | None:
    """Return the `TimbreFiscalDigital` element in *document*, or None."""
    root = safe_fromstring(document)
    return root.find(f".//{{{_TFD_NS}}}TimbreFiscalDigital")


def tfd_fields(tfd_el: etree._Element) -> dict[str, str | None]:
    """Return the TFD's own attributes as a plain dict."""
    return {attr: tfd_el.get(attr) for attr in _TFD_ATTRS}


def tfd_cadena_original(tfd_el: etree._Element) -> bytes:
    """Compute the TFD's own cadena original (Rubro III.B, `cadenaoriginal_TFD_1_1.xslt`).

    The transform matches on `/tfd:TimbreFiscalDigital` (the document
    root), so *tfd_el* is re-rooted into a standalone document before
    transforming — it is normally a nested `Comprobante/Complemento` child.
    """
    standalone_root = etree.Element(f"{{{_TFD_NS}}}TimbreFiscalDigital", nsmap={"tfd": _TFD_NS})
    for key, value in tfd_el.attrib.items():
        standalone_root.set(key, value)

    transform = etree.XSLT(etree.parse(str(_TFD_CADENA_ORIGINAL_XSLT)))
    result = transform(standalone_root)
    return str(result).encode("utf-8")
