"""Pre-publish audit: verify mcp-cfdi-mx coherence against mcp-einvoicing-core.

Run standalone (from the workspace root):
    uv run python mcp-cfdi-mx/audit/audit_vs_core.py
    uv run python mcp-cfdi-mx/audit/audit_vs_core.py --output mcp-cfdi-mx/audit/report.json
    uv run python mcp-cfdi-mx/audit/audit_vs_core.py --fail-on blocking

Exit codes:
    0  All checks passed
    1  Warnings only (non-blocking)
    2  Blocking failures found

Scaffold status (2026-09-01)
-----------------------------
The invoice-tree pathway is resolved (``_IS_EN16931_FAMILY = False``,
``CFDIComprobante``), so CHECK 1 (core interface coverage) runs for real.
Models (``CFDIComprobante``, ``MXEmisor``, ``MXReceptor``, ``CFDIConcepto``,
``Pagos20``) and RFC validation exist; MCP-exposed generate/validate/seal
tools do not yet — only ``mx__get_supported_scope`` is implemented. Several
core symbols (notably ``SelloDigitalSigner`` and the Schematron/XSD
validator classes) are therefore genuinely unused so far and reported as
WARNING-level [MISSING], not overridden — they are real future work, not a
deliberate design choice, so they should not be silenced with an
``OVERRIDE-REASON``. See roadmap-2026.md for the tracked next build phase.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mcp_einvoicing_core.audit import (
    SEVERITY_BLOCKING,
    SEVERITY_OK,
    AuditReport,
    CheckFinding,
    CheckResult,
    make_report,
    parse_audit_args,
    render_summary_table,
    run_check_core_coverage,
    run_check_version_compatibility,
)

_PACKAGE = "mcp-cfdi-mx"
_MODULE = "mcp_cfdi_mx"
_ROOT = Path(__file__).resolve().parent.parent
_PYPROJECT = _ROOT / "pyproject.toml"
_SOURCES = _ROOT / "specs" / "README.md"

# ---------------------------------------------------------------------------
# CHECK 1 configuration — country-specific constants
# ---------------------------------------------------------------------------

# CFDI 4.0 predates and has no EN 16931 lineage — non-EN16931 pathway,
# CFDIComprobante extends InvoiceDocument. Same determination as mcp-nfe-br.
# See context-library/countries/mx.md "Invoice-tree pathway".
_IS_EN16931_FAMILY: bool = False
_PRIMARY_INVOICE_CLASS: tuple[str, str] = ("mcp_cfdi_mx.models.invoice", "CFDIComprobante")

_MODULES: list[str] = [
    f"{_MODULE}.server",
    f"{_MODULE}.models.invoice",
    f"{_MODULE}.models.pagos",
    f"{_MODULE}.tools.scope",
]

_INTENTIONAL_OVERRIDES: dict[str, set[str]] = {
    "mcp_einvoicing_core.base_server": {
        # OVERRIDE-REASON: EInvoicingMCPServer is imported from the top-level mcp_einvoicing_core package in server.py, not from base_server directly
        "EInvoicingMCPServer",
    },
    "mcp_einvoicing_core.models": {
        # OVERRIDE-REASON: MXEmisor/MXReceptor extend InvoiceParty by narrowing CFDIComprobante's seller/buyer field types, not by importing PartyAddress/PaymentTerms/VATSummary directly — those are inherited, unused fields for Phase 1 (no address/payment-terms/vat-summary modeling yet)
        "PartyAddress",
        "PaymentTerms",
        "VATSummary",
        # OVERRIDE-REASON: RFC validation raises inline via a pydantic field_validator (ValueError), not via the TaxIdValidationResult wrapper type
        "TaxIdValidationResult",
    },
}


def _finding(check_id: str, tag: str, severity: str, symbol: str, message: str) -> CheckFinding:
    return CheckFinding(
        check_id=check_id, tag=tag, severity=severity, symbol=symbol, message=message
    )


def run_check_0() -> CheckResult:
    """CHECK 0 — scaffold gates that block implementation and publication."""
    result = CheckResult(check_id="CHECK_0", name="Scaffold gates")

    result.findings.append(
        _finding(
            "CHECK_0", "[OK]", SEVERITY_OK, "_IS_EN16931_FAMILY", "Invoice-tree pathway declared."
        )
    )

    server_mod = __import__(f"{_MODULE}.server", fromlist=["mcp", "main"])
    for attr in ("mcp", "main"):
        present = hasattr(server_mod, attr)
        result.findings.append(
            _finding(
                "CHECK_0",
                "[OK]" if present else "[MISSING]",
                SEVERITY_OK if present else SEVERITY_BLOCKING,
                f"server.{attr}",
                f"server.{attr} is {'present' if present else 'absent'}.",
            )
        )

    return result


def run_check_5() -> CheckResult:
    """CHECK 5 — normative spec sources are recorded with an authority URL."""
    result = CheckResult(check_id="CHECK_5", name="Spec sources")

    if not _SOURCES.exists():
        result.findings.append(
            CheckFinding(
                check_id="CHECK_5",
                tag="[MISSING]",
                severity=SEVERITY_BLOCKING,
                symbol="specs/README.md",
                message="specs/README.md is absent. One authority URL per standard is required.",
            )
        )
        return result

    text = _SOURCES.read_text(encoding="utf-8")
    unresolved = text.count("[NEED:")
    # Three rows carry a supplied local file but no independently-verified
    # canonical URL (catálogos, matriz de errores, TFD 1.1) — tracked as
    # `manual` watch entries per specs/README.md, matching the precedent
    # already accepted for BR primary law and FR AFNOR norms. Not blocking.
    result.findings.append(
        CheckFinding(
            check_id="CHECK_5",
            tag="[OK]" if unresolved == 0 else "[NEED]",
            severity=SEVERITY_OK,
            symbol="specs/README.md",
            message=(
                "All spec sources carry an authority URL and a retrieval date."
                if unresolved == 0
                else (
                    f"{unresolved} [NEED:] marker(s) remain for canonical URLs not yet "
                    "independently verified (tracked as `manual` regulatory-watch rows, "
                    "not blocking — the underlying local file is present)."
                )
            ),
        )
    )

    return result


def run_audit() -> AuditReport:
    """Execute all checks and return the aggregated AuditReport. No side effects."""
    report = make_report(_PACKAGE, _PYPROJECT)

    report.checks.append(run_check_0())
    report.checks.append(
        run_check_core_coverage(
            package_name=_PACKAGE,
            package_modules=_MODULES,
            intentional_overrides=_INTENTIONAL_OVERRIDES,
            is_en16931_family=_IS_EN16931_FAMILY,
            primary_invoice_class=_PRIMARY_INVOICE_CLASS,
        )
    )
    report.checks.append(
        run_check_version_compatibility(
            package_name=_PACKAGE,
            pyproject_path=_PYPROJECT,
        )
    )
    report.checks.append(run_check_5())

    return report


def main(argv: list[str] | None = None) -> int:
    args = parse_audit_args(f"Pre-publish audit: {_PACKAGE} vs mcp-einvoicing-core", argv)
    report = run_audit()

    output_path = Path(args.output) if args.output else _ROOT / "audit" / "report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

    if not args.quiet:
        print(render_summary_table(report))
        print(f"\nJSON report written to: {output_path}")

    if args.fail_on == "never":
        return 0
    if args.fail_on == "warnings":
        return min(report.exit_code, 2)
    return 2 if report.total_blocking > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
