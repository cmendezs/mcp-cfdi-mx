# Security Policy

## Supported versions

Security fixes are applied to the latest published minor release only. Older
versions do not receive backported patches; upgrade to the current release to
stay supported.

| Version | Supported |
|---|---|
| 0.1.x | Yes |
| < 0.1.0 | No |

## Reporting a vulnerability

Report suspected vulnerabilities privately through GitHub, not in a public
issue or pull request:

1. Go to the repository Security tab: https://github.com/cmendezs/mcp-cfdi-mx/security
2. Select **Report a vulnerability** to open a private security advisory.
3. Describe the issue, the affected version, and a minimal reproduction.

You will receive an acknowledgement on a best-effort basis. This is a
volunteer-maintained open-source project, so response times vary; please allow
a reasonable window before any public disclosure.

## Scope and data-handling note

These tools generate, validate, and (for local sealing) sign fiscal documents.
When you file a report, include only synthetic data. Never attach real RFC
values, production CSD certificates or private keys, PAC API tokens, or live
credentials to an advisory. Redact any such values from logs and reproductions
before sharing.

CSD private-key handling is a particular area of interest: this package takes
a file path or environment reference for key material, never a plaintext key
argument. Report any code path that deviates from that as a security issue.

## Out of scope

- Vulnerabilities in SAT's own platforms, or in third-party PACs (Proveedores
  Autorizados de Certificación) this package's output may be handed to. Report
  those to the operator concerned.
- Findings that require a compromised local machine or a malicious dependency
  already installed in the runtime.
