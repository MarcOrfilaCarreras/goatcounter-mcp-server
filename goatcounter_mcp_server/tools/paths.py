from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from goatcounter_mcp_server.client import GoatcounterClient
from goatcounter_mcp_server.dependencies import get_client


def register(mcp: FastMCP) -> None:
    """Register path tools."""

    @mcp.tool
    async def list_paths(
        limit: Annotated[
            int,
            Field(
                description="Number of paths to return (1-200).",
                ge=1,
                le=200,
            ),
        ] = 20,
        after: Annotated[
            int | None,
            Field(description="Return only paths with an ID greater than this."),
        ] = None,
        client: GoatcounterClient = Depends(get_client),
    ) -> dict[str, Any]:
        """List tracked paths, without statistics, for pagination or discovery."""

        return await client.list_paths(limit=limit, after=after)
