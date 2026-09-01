"""mx__verify_tfd — parse and verify a PAC-returned Timbre Fiscal Digital 1.1 stamp."""

from __future__ import annotations

import base64
from typing import Annotated

from lxml import etree

from mcp_cfdi_mx.utils.tfd import find_tfd, tfd_cadena_original, tfd_fields


def mx__verify_tfd(
    xml: Annotated[str, "The sealed, PAC-stamped CFDI XML (with a TimbreFiscalDigital complement)"],
    pac_certificado_der_b64: Annotated[
        str | None,
        (
            "Base64-encoded DER certificate of the PAC/SAT that stamped this TFD, "
            "used to cryptographically verify SelloSAT. SAT does not embed this "
            "certificate in the TFD itself, so it is not available without the "
            "caller supplying it. Omit to parse fields and compute the cadena "
            "original without verifying SelloSAT."
        ),
    ] = None,
) -> dict[str, object]:
    """Parse a Timbre Fiscal Digital 1.1 stamp and, optionally, verify SelloSAT.

    Always returns the TFD's own attributes (`UUID`, `FechaTimbrado`,
    `RfcProvCertif`, `SelloCFD`, `NoCertificadoSAT`, `SelloSAT`, ...) and the
    recomputed cadena original (via `cadenaoriginal_TFD_1_1.xslt`, per
    Anexo 20 Rubro III.B). If `pac_certificado_der_b64` is supplied,
    additionally verifies `SelloSAT` (SHA-256 + RSA-PKCS#1v1.5, the same
    algorithm as the emisor's own Sello) against that certificate's public
    key. Without it, `sello_sat_verified` is `null` — parsing succeeded but
    cryptographic verification was not attempted, not "passed".

    Returns a dict with:
    - ``found``: False if no `TimbreFiscalDigital` element exists in *xml*
    - ``fields``: the TFD's own attributes
    - ``cadena_original``: the recomputed cadena original string
    - ``sello_sat_verified``: True/False if `pac_certificado_der_b64` was
      supplied, else null
    """
    try:
        tfd_el = find_tfd(xml.encode("utf-8"))
    except (etree.XMLSyntaxError, ValueError) as exc:
        return {"found": False, "error": "xml_parse_error", "details": str(exc)}

    if tfd_el is None:
        return {"found": False}

    fields = tfd_fields(tfd_el)
    cadena_original = tfd_cadena_original(tfd_el)

    result: dict[str, object] = {
        "found": True,
        "fields": fields,
        "cadena_original": cadena_original.decode("utf-8"),
        "sello_sat_verified": None,
    }

    if pac_certificado_der_b64 is None:
        return result

    try:
        from cryptography.exceptions import InvalidSignature  # noqa: PLC0415
        from cryptography.hazmat.primitives import hashes  # noqa: PLC0415
        from cryptography.hazmat.primitives.asymmetric import padding, rsa  # noqa: PLC0415
        from cryptography.x509 import load_der_x509_certificate  # noqa: PLC0415
    except ImportError as exc:
        return {**result, "error": "import_error", "details": str(exc)}

    sello_sat = fields.get("SelloSAT")
    if not sello_sat:
        return {**result, "sello_sat_verified": False, "error": "no_sello_sat_to_verify"}

    cert = load_der_x509_certificate(base64.b64decode(pac_certificado_der_b64))
    public_key = cert.public_key()
    if not isinstance(public_key, rsa.RSAPublicKey):
        return {
            **result,
            "sello_sat_verified": False,
            "error": f"pac certificate contains a {type(public_key).__name__}, not RSA",
        }

    signature = base64.b64decode(sello_sat)
    try:
        public_key.verify(signature, cadena_original, padding.PKCS1v15(), hashes.SHA256())
        verified = True
    except InvalidSignature:
        verified = False

    return {**result, "sello_sat_verified": verified}
