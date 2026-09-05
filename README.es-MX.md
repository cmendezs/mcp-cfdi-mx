# mcp-cfdi-mx 🇲🇽

[English](README.md) | [Español](README.es-MX.md)

<!-- mcp-name: io.github.cmendezs/mcp-cfdi-mx -->

![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
[![PyPI version](https://img.shields.io/pypi/v/mcp-cfdi-mx.svg)](https://pypi.org/project/mcp-cfdi-mx/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-cfdi-mx.svg)](https://pypi.org/project/mcp-cfdi-mx/) [![mcp-cfdi-mx MCP server](https://glama.ai/mcp/servers/cmendezs/mcp-cfdi-mx/badges/score.svg)](https://glama.ai/mcp/servers/cmendezs/mcp-cfdi-mx)

Un servidor MCP en Python que provee herramientas para la **facturación electrónica** mexicana conforme al **CFDI 4.0** y al **Complemento de Pagos 2.0**, según el estándar técnico Anexo 20 del SAT. Permite a agentes de IA (Claude, IDEs) construir, validar contra el XSD y sellar documentos CFDI 4.0 (Ingreso, Egreso y Complemento de Pagos 2.0), verificar un Timbre Fiscal Digital devuelto por un PAC, y validar RFCs mexicanos.

**Alcance de la Fase 1.** Este paquete cubre únicamente CFDI 4.0 Ingreso, Egreso y Complemento de Pagos 2.0 — Carta Porte, Complemento de Nómina, Retenciones y Comercio Exterior aún no están soportados, y no realiza el envío a ningún PAC. Ver [Herramientas disponibles](#herramientas-disponibles) para el detalle exacto de lo implementado hoy.

---

## Introducción

Este paquete está construido sobre [**mcp-einvoicing-core**](https://github.com/cmendezs/mcp-einvoicing-core), la biblioteca base compartida para servidores MCP de facturación electrónica. Provee el modelo base `InvoiceDocument`, el validador de RFC `TaxIdentifier.validate_mx_rfc`, y `SelloDigitalSigner` — la implementación concreta específica de México de la abstracción de firma de documentos de core (digestión SHA-256 de la cadena original, firmada con RSA-PKCS#1v1.5 usando el CSD del emisor, conforme al Anexo 20 del SAT).

`mcp-einvoicing-core` se instala automáticamente como dependencia, no se requiere ningún paso adicional.

El CFDI es un estándar de **modelo de aclaración (clearance)**: un CFDI adquiere validez legal únicamente hasta que un PAC (Proveedor Autorizado de Certificación) lo certifica y devuelve un Timbre Fiscal Digital (TFD). Este paquete no realiza el envío a un PAC — es **agnóstico al PAC**, produciendo ya sea un CFDI sellado localmente (listo para entregar a cualquier PAC que acepte documentos pre-sellados) o un CFDI sin sellar y válido contra el esquema (para un PAC que sella en representación del emisor), seleccionado mediante el parámetro `sealing_mode`.

## Instalación

### Vía PyPI (recomendado)

```bash
pip install mcp-cfdi-mx
```

O sin instalación previa usando `uvx`:

```bash
uvx mcp-cfdi-mx
```

### Desde el código fuente

```bash
git clone https://github.com/cmendezs/mcp-cfdi-mx.git
cd mcp-cfdi-mx
uv sync --all-extras
```

## Configuración (variables de entorno)

Este paquete no tiene variables de entorno requeridas. Las rutas y contraseñas del certificado/llave del CSD se
pasan como argumentos de las herramientas (rutas de archivo o referencias de entorno — nunca material de
llave en texto plano dentro de una solicitud), no se leen de una variable de entorno fija.

## Integración con Claude Desktop

Agrega la siguiente configuración a tu archivo `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cfdi-mx": {
      "command": "uvx",
      "args": ["mcp-cfdi-mx"]
    }
  }
}
```

## Integración con Cursor

Cursor soporta servidores MCP vía stdio. Agrega la configuración en:
- **Global** (todos los proyectos): `~/.cursor/mcp.json`
- **Por proyecto** (solo este repositorio): `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "cfdi-mx": {
      "command": "uvx",
      "args": ["mcp-cfdi-mx"]
    }
  }
}
```

Recarga la ventana de Cursor (`Ctrl+Shift+P` → *Reload Window*) después de guardar los cambios.

## Integración con Kiro

Kiro soporta servidores MCP a través de un archivo de configuración dedicado:
- **Global**: `~/.kiro/settings/mcp.json`
- **Workspace**: `.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "cfdi-mx": {
      "command": "uvx",
      "args": ["mcp-cfdi-mx"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

> **Consejo de seguridad**: si una versión futura de las herramientas acepta credenciales vía referencia de
> entorno, usa la sintaxis `"VAR_NAME": "${VAR_NAME}"` para que Kiro las resuelva desde el shell en lugar
> de almacenarlas en texto plano.

## Herramientas disponibles

### Construcción

| Herramienta | Descripción |
|------|-------------|
| `mx__build_cfdi` | Construye un XML de `Comprobante` CFDI 4.0 bien formado y sin sellar (Ingreso o Egreso) a partir de datos estructurados |
| `mx__build_pago` | Construye un CFDI de Complemento de Pagos 2.0 (`TipoDeComprobante="P"`), componiendo el envoltorio de `Concepto` único y fijo que exige la guía del SAT |

### Validación y sellado

| Herramienta | Descripción |
|------|-------------|
| `mx__validate_cfdi` | Validación completa contra el XSD de `cfdv40.xsd`, más `TimbreFiscalDigitalv11.xsd.xml` y/o `Pagos20.xsd.xml` cuando esos complementos están presentes |
| `mx__seal_cfdi` | Calcula el Sello Digital vía `SelloDigitalSigner`, consciente de `sealing_mode` (`"local"` \| `"pac"`) |
| `mx__verify_tfd` | Analiza un Timbre Fiscal Digital 1.1 devuelto por un PAC, y verifica criptográficamente `SelloSAT` cuando se proporciona el certificado del PAC |

### Alcance

| Herramienta | Descripción |
|------|-------------|
| `mx__get_supported_scope` | Devuelve los tipos de documento CFDI, complementos y modos de sellado que este paquete soporta actualmente |

Ver [`docs/TOOLS.md`](docs/TOOLS.md) para la referencia completa de parámetros de cada herramienta, generada a partir del registro de herramientas en ejecución.

### Aún no implementado

El transporte de envío al PAC (este paquete es agnóstico al PAC y no envía a ningún PAC específico), y los complementos de fases posteriores (Carta Porte, Complemento de Nómina, Retenciones, Comercio Exterior) — rastreados en `context-library/roadmap-2026.md` (repositorio raíz del workspace).

## Arquitectura

`mcp_cfdi_mx.models.CFDIComprobante` extiende `mcp_einvoicing_core.models.InvoiceDocument` (la
ruta no-EN 16931 — el CFDI es anterior y no tiene relación con CEN TC 434, la misma determinación
que `mcp-nfe-br`). La validación de RFC tanto para Emisor como Receptor pasa por
`TaxIdentifier.validate_mx_rfc` (core). El sellado pasa por
`mcp_einvoicing_core.digital_signature.SelloDigitalSigner`, la implementación concreta específica de
México de `BaseDocumentSigner` de core — el mismo patrón que usan ES (XAdES), BR (XML-DSig)
e IT (CAdES) para sus propios estándares de firma.

```text
[ ERP System / Application ] <--> [ MCP Server ] <--> [ PAC (any, PAC-agnostic) / SAT ]
          ^                           |
          |                           v
   [ AI Agent (Claude) ] <--- (CFDI 4.0 / Pagos 2.0)
```

## Estándares soportados

| Estándar | Versión | Fuente |
|---|---|---|
| CFDI (Comprobante Fiscal Digital por Internet) | 4.0 | Anexo 20 del SAT, DOF 2022-01-13 |
| Timbre Fiscal Digital | 1.1 | SAT |
| Complemento de Pagos | 2.0 | SAT |

Ver [`specs/README.md`](specs/README.md) para el paquete completo de fuentes y sus fechas de obtención, y
[`context-library/countries/mx.md`](https://github.com/cmendezs/mcp-einvoicing/blob/main/context-library/countries/mx.md)
en el repositorio raíz del workspace para la referencia de cumplimiento verificada.

## Pruebas

```bash
uv run pytest tests/ -v
```

## Contribuciones

Las contribuciones son bienvenidas — ver [CONTRIBUTING.md](CONTRIBUTING.md) para las guías.

## Other e-invoicing MCP servers

| Country | Server |
|---------|--------|
| 🌍 Global | [mcp-einvoicing-core](https://github.com/cmendezs/mcp-einvoicing-core) |
| 🇦🇪 United Arab Emirates | [mcp-einvoicing-ae](https://github.com/cmendezs/mcp-einvoicing-ae) |
| 🇧🇪 Belgium | [mcp-einvoicing-be](https://github.com/cmendezs/mcp-einvoicing-be) |
| 🇧🇷 Brazil | [mcp-nfe-br](https://github.com/cmendezs/mcp-nfe-br) |
| 🇫🇷 France | [mcp-facture-electronique-fr](https://github.com/cmendezs/mcp-facture-electronique-fr) |
| 🇩🇪 Germany | [mcp-einvoicing-de](https://github.com/cmendezs/mcp-einvoicing-de) |
| 🇮🇹 Italy | [mcp-fattura-elettronica-it](https://github.com/cmendezs/mcp-fattura-elettronica-it) |
| 🇲🇽 Mexico | [mcp-cfdi-mx](https://github.com/cmendezs/mcp-cfdi-mx) |
| 🇵🇱 Poland | [mcp-ksef-pl](https://github.com/cmendezs/mcp-ksef-pl) |
| 🇸🇬 Singapore | [mcp-invoicenow-sg](https://github.com/cmendezs/mcp-invoicenow-sg) |
| 🇪🇸 Spain | [mcp-facturacion-electronica-es](https://github.com/cmendezs/mcp-facturacion-electronica-es) |

## Licencia

Este proyecto se distribuye bajo la licencia **Apache 2.0**.
Ver el archivo [LICENSE](LICENSE) para más detalles. Para el historial completo de versiones, ver [CHANGELOG.md](CHANGELOG.md).
