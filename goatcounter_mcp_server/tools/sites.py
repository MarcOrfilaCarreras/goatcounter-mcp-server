from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from fastmcp.dependencies import Depends

from goatcounter_mcp_server.client import GoatcounterClient
from goatcounter_mcp_server.dependencies import get_client


def register(mcp: FastMCP) -> None:
    """Register user and site tools."""

    @mcp.tool
    async def get_me(
        client: GoatcounterClient = Depends(get_client),
    ) -> dict[str, Any]:
        """Get the GoatCounter user and API token for this request's credentials."""

        return await client.get_me()

    @mcp.tool
    async def list_sites(
        client: GoatcounterClient = Depends(get_client),
    ) -> dict[str, Any]:
        """List every GoatCounter site this request's API token can access."""

        return await client.list_sites()
