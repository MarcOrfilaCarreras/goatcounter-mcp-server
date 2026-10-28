from __future__ import annotations

from fastmcp import FastMCP

from goatcounter_mcp_server.tools import register_tools

HOST = "0.0.0.0"
PORT = 8000


def create_server() -> FastMCP:
    """Create and configure a new server instance."""

    mcp = FastMCP(
        name="Goatcounter",
        instructions="""
Query GoatCounter analytics.

Credentials are supplied by the client on every request and are never stored by
this server. Send these HTTP headers with every MCP request:

- X-Goatcounter-URL: the full base URL of the GoatCounter instance, for example
  https://stats.example.com or https://mycode.goatcounter.com.
- X-Goatcounter-Token: a GoatCounter API token.

If either header is missing, the tools return an explanatory error.
""".strip(),
        cache_ttl=300,
        cache_scope="public",
    )
    register_tools(mcp)
    return mcp


mcp = create_server()


def main() -> None:
    """Run the server over stateless Streamable HTTP."""

    mcp.run(
        transport="http",
        host=HOST,
        port=PORT,
        stateless_http=True,
    )
