from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers

from goatcounter_mcp_server.client import GoatcounterClient
from goatcounter_mcp_server.credentials import (
    GoatcounterCredentials,
    GoatcounterCredentialsError,
)


def get_credentials() -> GoatcounterCredentials:
    """Read GoatCounter credentials from the current HTTP request."""

    return GoatcounterCredentials.from_headers(get_http_headers(include_all=True))


@asynccontextmanager
async def get_client() -> AsyncIterator[GoatcounterClient]:
    """Yield a GoatCounter API client scoped to the current request."""

    try:
        credentials = get_credentials()
    except GoatcounterCredentialsError as exc:
        # FastMCP surfaces ToolError messages to the client; a plain exception
        # would be replaced with a generic "failed to resolve dependency".
        raise ToolError(str(exc)) from exc

    async with GoatcounterClient(credentials) as client:
        yield client
