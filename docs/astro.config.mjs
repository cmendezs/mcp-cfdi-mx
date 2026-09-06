import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import starlightLlmsTxt from "starlight-llms-txt";

export default defineConfig({
  site: "https://cmendezs.github.io",
  base: "/mcp-cfdi-mx/",
  integrations: [
    starlight({
      title: "mcp-cfdi-mx",
      description: "MCP server for Mexican electronic invoicing (CFDI 4.0, Complemento de Pagos 2.0)",
      customCss: ["./src/styles/docs-theme.css"],
      social: [
        { icon: "github", label: "GitHub", href: "https://github.com/cmendezs/mcp-cfdi-mx" },
      ],
      locales: {
        root: { label: "English", lang: "en" },
        "es-mx": { label: "Español (México)", lang: "es-MX" },
      },
      sidebar: [
        { label: "Overview", link: "/" },
        { label: "Tools", link: "/tools/" },
        { label: "Changelog", link: "/changelog/" },
        { label: "Contributing", link: "/contributing/" },
        { label: "Security", link: "/security/" },
        { label: "Code of Conduct", link: "/code-of-conduct/" },
      ],
      plugins: [
        starlightLlmsTxt({
          projectName: "mcp-cfdi-mx",
          description: "MCP server for Mexican electronic invoicing (CFDI 4.0, Complemento de Pagos 2.0)",
          customSets: [
            {
              label: "Key links",
              description: "PyPI and MCP registry entries",
              links: ["https://pypi.org/project/mcp-cfdi-mx/", "https://registry.modelcontextprotocol.io/v0/servers?search=io.github.cmendezs/mcp-cfdi-mx"],
            },
          ],
        }),
      ],
    }),
  ],
});
