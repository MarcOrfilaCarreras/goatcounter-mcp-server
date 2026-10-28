from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from goatcounter_mcp_server.client import GoatcounterClient
from goatcounter_mcp_server.dependencies import get_client

StartDate = Annotated[
    str | None,
    Field(
        description=(
            "Start of the period in UTC, as 'YYYY-MM-DD', 'YYYY-MM-DD HH:MM:SS', "
            "or an ISO timestamp."
        )
    ),
]
EndDate = Annotated[
    str | None,
    Field(
        description=(
            "End of the period in UTC, as 'YYYY-MM-DD', 'YYYY-MM-DD HH:MM:SS', "
            "or an ISO timestamp. A date-only value includes the whole day."
        )
    ),
]
StatsLimit = Annotated[
    int,
    Field(description="Number of results to return (1-100).", ge=1, le=100),
]
StatsOffset = Annotated[
    int | None,
    Field(description="Offset for pagination.", ge=0),
]
IncludePaths = Annotated[
    list[int] | None,
    Field(description="Only include these GoatCounter path IDs."),
]
ExcludeEvents = Annotated[
    bool,
    Field(
        description=(
            "Exclude event hits from pageview results. Defaults to true; set to "
            "false to include events."
        )
    ),
]


def register(mcp: FastMCP) -> None:
    """Register statistics tools."""

    @mcp.tool
    async def get_stats_total(
        start: StartDate = None,
        end: EndDate = None,
        include_paths: IncludePaths = None,
        exclude_events: ExcludeEvents = True,
        client: GoatcounterClient = Depends(get_client),
    ) -> dict[str, Any]:
        """Get total pageview and visitor counts for a period.

        Events are excluded from the total by default; their count is returned
        separately as ``total_events``.
        """

        return await client.get_stats_total(
            start=start,
            end=end,
            include_paths=include_paths,
            exclude_events=exclude_events,
        )

    @mcp.tool
    async def get_stats_hits(
        start: StartDate = None,
        end: EndDate = None,
        limit: StatsLimit = 20,
        group: Annotated[
            Literal["hour", "day", "week", "month"] | None,
            Field(
                description=(
                    "Grouping used for the maximum value in the response. Defaults to hourly."
                )
            ),
        ] = None,
        include_paths: IncludePaths = None,
        exclude_paths: Annotated[
            list[int] | None,
            Field(description="Exclude these GoatCounter path IDs."),
        ] = None,
        exclude_events: ExcludeEvents = True,
        client: GoatcounterClient = Depends(get_client),
    ) -> dict[str, Any]:
        """Get pageview and visitor statistics per path.

        Event rows are removed from the returned page by default so they do not
        appear as pageviews.
        """

        return await client.get_stats_hits(
            start=start,
            end=end,
            limit=limit,
            group=group,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            exclude_events=exclude_events,
        )

    @mcp.tool
    async def get_stats_refs(
        start: StartDate = None,
        end: EndDate = None,
        limit: StatsLimit = 20,
        offset: StatsOffset = None,
        include_paths: IncludePaths = None,
        client: GoatcounterClient = Depends(get_client),
    ) -> dict[str, Any]:
        """Get referrer statistics."""

        return await client.get_stats_page(
            "toprefs",
            start=start,
            end=end,
            limit=limit,
            offset=offset,
            include_paths=include_paths,
        )

    @mcp.tool
    async def get_stats_campaigns(
        start: StartDate = None,
        end: EndDate = None,
        limit: StatsLimit = 20,
        offset: StatsOffset = None,
        include_paths: IncludePaths = None,
        client: GoatcounterClient = Depends(get_client),
    ) -> dict[str, Any]:
        """Get campaign statistics."""

        return await client.get_stats_page(
            "campaigns",
            start=start,
            end=end,
            limit=limit,
            offset=offset,
            include_paths=include_paths,
        )

    @mcp.tool
    async def get_stats_browsers(
        start: StartDate = None,
        end: EndDate = None,
        limit: StatsLimit = 20,
        offset: StatsOffset = None,
        include_paths: IncludePaths = None,
        client: GoatcounterClient = Depends(get_client),
    ) -> dict[str, Any]:
        """Get browser statistics."""

        return await client.get_stats_page(
            "browsers",
            start=start,
            end=end,
            limit=limit,
            offset=offset,
            include_paths=include_paths,
        )

    @mcp.tool
    async def get_stats_systems(
        start: StartDate = None,
        end: EndDate = None,
        limit: StatsLimit = 20,
        offset: StatsOffset = None,
        include_paths: IncludePaths = None,
        client: GoatcounterClient = Depends(get_client),
    ) -> dict[str, Any]:
        """Get operating system statistics."""

        return await client.get_stats_page(
            "systems",
            start=start,
            end=end,
            limit=limit,
            offset=offset,
            include_paths=include_paths,
        )

    @mcp.tool
    async def get_stats_sizes(
        start: StartDate = None,
        end: EndDate = None,
        limit: StatsLimit = 20,
        offset: StatsOffset = None,
        include_paths: IncludePaths = None,
        client: GoatcounterClient = Depends(get_client),
    ) -> dict[str, Any]:
        """Get screen size statistics."""

        return await client.get_stats_page(
            "sizes",
            start=start,
            end=end,
            limit=limit,
            offset=offset,
            include_paths=include_paths,
        )

    @mcp.tool
    async def get_stats_locations(
        start: StartDate = None,
        end: EndDate = None,
        limit: StatsLimit = 20,
        offset: StatsOffset = None,
        include_paths: IncludePaths = None,
        client: GoatcounterClient = Depends(get_client),
    ) -> dict[str, Any]:
        """Get visitor location statistics."""

        return await client.get_stats_page(
            "locations",
            start=start,
            end=end,
            limit=limit,
            offset=offset,
            include_paths=include_paths,
        )
