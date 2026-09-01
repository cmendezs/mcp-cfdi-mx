"""XSD validators for CFDI 4.0, TFD 1.1, and Complemento de Pagos 2.0.

SAT's schemas `xs:import` each other by absolute `http://www.sat.gob.mx/...`
URL (`cfdv40.xsd.xml` imports `catCFDI.xsd`/`tdCFDI.xsd`; `Pagos20.xsd.xml`
additionally imports `catPagos.xsd.xml`). None of that resolves offline, so
each validator here compiles its schema through a resolver that maps the
known import URLs to the local files bundled under `specs/`, mirroring
`mcp_einvoicing_core.digital_signature.SelloDigitalSigner`'s own resolver for
the cadena original XSLT includes.

Subclasses `mcp_einvoicing_core.schematron.BaseXSDValidator` rather than
using the concrete `XSDValidator` directly, since that class's constructor
has no resolver hook — this is exactly the "needs custom compilation"
extension point `BaseXSDValidator`'s own docstring documents.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree
from mcp_einvoicing_core.schematron import BaseXSDValidator, ValidationMessage, ValidationResult
from mcp_einvoicing_core.xml_utils import safe_fromstring

_SPECS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "specs"

CFDI_TARGET_NS = "http://www.sat.gob.mx/cfd/4"
_TFD_TARGET_NS = "http://www.sat.gob.mx/TimbreFiscalDigital"
_PAGOS_TARGET_NS = "http://www.sat.gob.mx/Pagos20"

_CAT_CFDI_URL = "http://www.sat.gob.mx/sitio_internet/cfd/catalogos/catCFDI.xsd"
_TD_CFDI_URL = "http://www.sat.gob.mx/sitio_internet/cfd/tipoDatos/tdCFDI/tdCFDI.xsd"
_CAT_PAGOS_URL = "http://www.sat.gob.mx/sitio_internet/cfd/catalogos/Pagos/catPagos.xsd"

_SHARED_IMPORTS: dict[str, str] = {
    _CAT_CFDI_URL: str(_SPECS_DIR / "catCFDI.xsd"),
    _TD_CFDI_URL: str(_SPECS_DIR / "tdCFDI.xsd"),
}


class _KnownURLResolver(etree.Resolver):
    """Resolve a fixed map of SAT import URLs (or synthetic local keys) to local files."""

    def __init__(self, known: dict[str, str]) -> None:
        super().__init__()
        self._known = known

    def resolve(self, url: str, pubid: object, context: object) -> object:  # type: ignore[override]
        if url in self._known:
            return self.resolve_filename(self._known[url], context)  # type: ignore[attr-defined]
        return None


class _ResolvedXSDValidator(BaseXSDValidator):
    """Same validation logic as core's `XSDValidator`, with resolver-aware compilation."""

    def __init__(self, schema: etree.XMLSchema) -> None:
        self._schema = schema

    @classmethod
    def from_entry_point(
        cls, entry_path: Path, known_imports: dict[str, str]
    ) -> _ResolvedXSDValidator:
        """Compile *entry_path* directly as the schema document."""
        if not entry_path.exists():
            raise FileNotFoundError(f"XSD schema not found: {entry_path}.")
        parser = etree.XMLParser()
        parser.resolvers.add(_KnownURLResolver(known_imports))
        try:
            tree = etree.parse(str(entry_path), parser)
            schema = etree.XMLSchema(tree)
        except etree.XMLSchemaParseError as exc:
            raise ValueError(f"Failed to parse XSD schema {entry_path}: {exc}") from exc
        return cls(schema)

    def validate(self, document: bytes, *, profile: str = "", syntax: str = "") -> ValidationResult:
        try:
            doc = safe_fromstring(document)
        except etree.XMLSyntaxError as exc:
            return ValidationResult(
                is_valid=False,
                errors=[
                    ValidationMessage(
                        severity="error", rule_id="XML-PARSE", location="/", text=str(exc)
                    )
                ],
                profile=profile,
                syntax=syntax,
            )

        if self._schema.validate(doc):
            return ValidationResult(is_valid=True, profile=profile, syntax=syntax)

        errors = [
            ValidationMessage(
                severity="error",
                rule_id="XSD",
                location=f"line {entry.line}",
                text=entry.message,
            )
            for entry in self._schema.error_log  # type: ignore[attr-defined]
        ]
        return ValidationResult(is_valid=False, errors=errors, profile=profile, syntax=syntax)


def cfdi_validator() -> _ResolvedXSDValidator:
    """XSD validator for a bare CFDI 4.0 `Comprobante` (no `Complemento` contents checked).

    `Complemento`'s `xs:any` wildcard defaults to `processContents="strict"`
    (the XSD spec default when unspecified — confirmed in `cfdv40.xsd.xml`,
    the element has no explicit `processContents` attribute), so any
    complement content inside it fails strict validation unless that
    complement's own global element is also loaded into the same schema. Use
    `full_validator()` to validate a `Comprobante` that carries a
    `Complemento` (TFD, Pagos, or both) — this validator alone will report a
    "no matching global element declaration" error for any of them, which is
    a limitation of this narrower schema, not the document.
    """
    return _ResolvedXSDValidator.from_entry_point(_SPECS_DIR / "cfdv40.xsd.xml", _SHARED_IMPORTS)


def full_validator(
    *, include_tfd: bool = False, include_pagos: bool = False
) -> _ResolvedXSDValidator:
    """XSD validator combining `cfdv40.xsd` with the requested complement schemas.

    Compiles a synthetic in-memory schema that `xs:import`s `cfdv40.xsd.xml`
    plus whichever complement schemas are requested, all resolved through
    the same local-file resolver — the standard libxml2 technique for
    validating a document against multiple target-namespace schemas at
    once, needed because `Complemento`'s `xs:any` wildcard is strict (see
    `cfdi_validator()`'s docstring).
    """
    imports = [f'<xs:import namespace="{CFDI_TARGET_NS}" schemaLocation="cfdv40.xsd.xml"/>']
    known_imports = dict(_SHARED_IMPORTS)
    known_imports["cfdv40.xsd.xml"] = str(_SPECS_DIR / "cfdv40.xsd.xml")

    if include_tfd:
        imports.append(
            f'<xs:import namespace="{_TFD_TARGET_NS}" schemaLocation="TimbreFiscalDigitalv11.xsd.xml"/>'
        )
        known_imports["TimbreFiscalDigitalv11.xsd.xml"] = str(
            _SPECS_DIR / "TimbreFiscalDigitalv11.xsd.xml"
        )
    if include_pagos:
        imports.append(
            f'<xs:import namespace="{_PAGOS_TARGET_NS}" schemaLocation="Pagos20.xsd.xml"/>'
        )
        known_imports["Pagos20.xsd.xml"] = str(_SPECS_DIR / "Pagos20.xsd.xml")
        known_imports[_CAT_PAGOS_URL] = str(_SPECS_DIR / "catPagos.xsd.xml")

    synthetic = (
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
        + "".join(imports)
        + "</xs:schema>"
    )

    parser = etree.XMLParser()
    parser.resolvers.add(_KnownURLResolver(known_imports))
    root = etree.fromstring(synthetic.encode("utf-8"), parser)
    schema = etree.XMLSchema(etree.ElementTree(root))
    return _ResolvedXSDValidator(schema)


def tfd_validator() -> _ResolvedXSDValidator:
    """XSD validator for a standalone `TimbreFiscalDigital` element (`TimbreFiscalDigitalv11.xsd.xml`)."""
    return _ResolvedXSDValidator.from_entry_point(
        _SPECS_DIR / "TimbreFiscalDigitalv11.xsd.xml", {_TD_CFDI_URL: _SHARED_IMPORTS[_TD_CFDI_URL]}
    )


def pagos_validator() -> _ResolvedXSDValidator:
    """XSD validator for a standalone `Pagos` complement element (`Pagos20.xsd.xml`)."""
    imports = dict(_SHARED_IMPORTS)
    imports[_CAT_PAGOS_URL] = str(_SPECS_DIR / "catPagos.xsd.xml")
    return _ResolvedXSDValidator.from_entry_point(_SPECS_DIR / "Pagos20.xsd.xml", imports)
