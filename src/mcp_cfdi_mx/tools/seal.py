"""mx__seal_cfdi — compute the Sello Digital via SelloDigitalSigner, sealing_mode-aware."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from mcp_einvoicing_core.digital_signature import SelloDigitalSigner, SelloDigitalSignerConfig

_SPECS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "specs"
_CADENA_ORIGINAL_XSLT = _SPECS_DIR / "cadenaoriginal_4_0.xslt"
_XSLT_INCLUDE_PATHS = {
    "http://www.sat.gob.mx/sitio_internet/cfd/2/cadenaoriginal_2_0/utilerias.xslt": str(
        _SPECS_DIR / "utilerias.xslt"
    ),
    "http://www.sat.gob.mx/sitio_internet/cfd/Pagos/Pagos20.xslt": str(_SPECS_DIR / "Pagos20.xslt"),
}


def mx__seal_cfdi(
    xml: Annotated[
        str, "The unsealed CFDI 4.0 Comprobante XML, as returned by mx__build_cfdi/mx__build_pago"
    ],
    sealing_mode: Annotated[
        Literal["local", "pac"],
        (
            "'local': compute Sello/NoCertificado/Certificado from the supplied CSD. "
            "'pac': return the XML unchanged, for a PAC that seals on the emisor's behalf."
        ),
    ],
    cert_path: Annotated[
        str | None,
        "Path to the CSD's DER-encoded certificate (.cer). Required when sealing_mode='local'.",
    ] = None,
    key_path: Annotated[
        str | None,
        "Path to the CSD's encrypted PKCS#8 DER private key (.key). Required when sealing_mode='local'.",
    ] = None,
    key_password: Annotated[
        str | None,
        (
            "Passphrase for the private key. Required when sealing_mode='local'. This is "
            "a secret that transits the tool call as plain text — callers should source it "
            "from an environment variable or secrets manager reference on their side rather "
            "than hardcoding it, the same as cert_path/key_path are file references rather "
            "than inline key material."
        ),
    ] = None,
    no_certificado: Annotated[
        str | None,
        (
            "The CSD's 20-digit serial number from the SAT enrollment acknowledgment "
            "(acuse). Not derived from the certificate bytes — no confirmed algorithm "
            "exists for that derivation, see SelloDigitalSigner's docstring. Required "
            "when sealing_mode='local'."
        ),
    ] = None,
) -> dict[str, object]:
    """Seal (or deliberately not seal) a CFDI 4.0 Comprobante, PAC-agnostic.

    `sealing_mode="local"` computes the cadena original via the actual SAT
    XSLT transform (`specs/cadenaoriginal_4_0.xslt`, with its `utilerias.xslt`
    and `Pagos20.xslt` includes resolved from `specs/`; any other complemento
    include a document might reference is not in Phase-1 scope and stubs to
    a no-op template — see `SelloDigitalSigner`'s docstring), then computes
    `Sello`/`NoCertificado`/`Certificado` via
    `mcp_einvoicing_core.digital_signature.SelloDigitalSigner` — no local
    reimplementation of the signing algorithm.

    `sealing_mode="pac"` returns *xml* unchanged: some PACs accept an
    unsealed, schema-valid CFDI and seal it on the emisor's behalf. This
    tool does not submit to any PAC — see the package README for the
    PAC-agnostic design.

    CSD key material is always a file path, never accepted as plaintext key
    content in a tool argument.

    Returns a dict with:
    - ``xml``: the sealed (or, for ``"pac"``, unchanged) XML string
    - ``sealing_mode``: echoes the mode used
    """
    if sealing_mode == "pac":
        return {"xml": xml, "sealing_mode": "pac"}

    missing = [
        name
        for name, value in (
            ("cert_path", cert_path),
            ("key_path", key_path),
            ("key_password", key_password),
            ("no_certificado", no_certificado),
        )
        if value is None
    ]
    if missing:
        return {
            "error": "missing_arguments",
            "details": f"sealing_mode='local' requires: {', '.join(missing)}",
        }

    config = SelloDigitalSignerConfig(
        cert_path=cert_path,  # type: ignore[arg-type]
        key_path=key_path,  # type: ignore[arg-type]
        key_password=key_password,  # type: ignore[arg-type]
        no_certificado=no_certificado,  # type: ignore[arg-type]
        cadena_original_xslt_path=str(_CADENA_ORIGINAL_XSLT),
        xslt_include_paths=_XSLT_INCLUDE_PATHS,
    )

    try:
        sealed = SelloDigitalSigner(config).sign(xml.encode("utf-8"))
    except (FileNotFoundError, ValueError, ImportError) as exc:
        return {"error": "sealing_error", "details": str(exc)}

    return {"xml": sealed.decode("utf-8"), "sealing_mode": "local"}
