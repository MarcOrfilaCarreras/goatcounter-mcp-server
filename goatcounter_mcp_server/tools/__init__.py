from fastmcp import FastMCP

from goatcounter_mcp_server.tools import paths, sites, stats


def register_tools(mcp: FastMCP) -> None:
    """Register every GoatCounter tool on the given server."""

    sites.register(mcp)
    paths.register(mcp)
    stats.register(mcp)


__all__ = ["register_tools"]
