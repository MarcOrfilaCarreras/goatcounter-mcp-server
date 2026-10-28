from __future__ import annotations

import asyncio
import logging
import random
from datetime import date, datetime, time, timezone
from typing import Any

import httpx

from goatcounter_mcp_server.credentials import GoatcounterCredentials

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
BASE_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 30.0
DEFAULT_TIMEOUT_SECONDS = 30.0


class GoatcounterAPIError(Exception):
    """Raised when the GoatCounter API returns an error or is unreachable."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class GoatcounterClient:
    """A short-lived client bound to one request's credentials."""

    def __init__(
        self,
        credentials: GoatcounterCredentials,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._instance_url = credentials.instance_url
        self._api_base = f"{self._instance_url}/api/v0"
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {credentials.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "goatcounter-mcp-server",
            },
        )

    async def __aenter__(self) -> GoatcounterClient:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._api_base}{endpoint}"

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = await self._client.get(url, params=params)
            except httpx.RequestError as exc:
                raise GoatcounterAPIError(
                    f"Could not reach the GoatCounter instance at {self._instance_url}: {exc}"
                ) from exc

            if response.status_code == 429:
                if attempt == MAX_ATTEMPTS:
                    raise GoatcounterAPIError(
                        f"GoatCounter rate limit exceeded after {MAX_ATTEMPTS} attempts.",
                        status_code=429,
                    )

                delay = _retry_delay(response.headers, attempt)
                logger.warning(
                    "GoatCounter rate limit reached; retrying in %.2fs (attempt %d/%d).",
                    delay,
                    attempt,
                    MAX_ATTEMPTS,
                )
                await asyncio.sleep(delay)
                continue

            if response.is_error:
                raise _error_from_response(response)

            if response.status_code in {202, 204}:
                return None

            try:
                return response.json()
            except ValueError as exc:
                raise GoatcounterAPIError(
                    f"GoatCounter returned a non-JSON response (HTTP {response.status_code}).",
                    status_code=response.status_code,
                ) from exc

        raise GoatcounterAPIError("GoatCounter request failed after all retries.")

    async def get_me(self) -> dict[str, Any]:
        """Get the user and API token associated with the request credentials."""

        return await self._request("/me")

    async def list_sites(self) -> dict[str, Any]:
        """List all sites accessible with the request credentials."""

        return await self._request("/sites")

    async def list_paths(
        self,
        *,
        limit: int = 20,
        after: int | None = None,
    ) -> dict[str, Any]:
        """List tracked paths, without statistics."""

        params: dict[str, Any] = {"Limit": limit}
        if after is not None:
            params["After"] = after

        return await self._request("/paths", params=params)

    async def get_stats_total(
        self,
        *,
        start: str | None = None,
        end: str | None = None,
        include_paths: list[int] | None = None,
        exclude_events: bool = True,
    ) -> dict[str, Any]:
        """Get total pageview and visitor counts for a period.

        GoatCounter's ``total`` includes event hits. Unless ``exclude_events``
        is false, subtract ``total_events`` so ``total`` only counts pageviews.
        """

        params = _stats_params(start=start, end=end, include_paths=include_paths)
        data = await self._request("/stats/total", params=params)

        if exclude_events and isinstance(data, dict):
            _remove_events_from_total(data)

        return data

    async def get_stats_hits(
        self,
        *,
        start: str | None = None,
        end: str | None = None,
        limit: int = 20,
        group: str | None = None,
        include_paths: list[int] | None = None,
        exclude_paths: list[int] | None = None,
        exclude_events: bool = True,
    ) -> dict[str, Any]:
        """Get pageview and visitor statistics per path.

        Event hits are removed from the result by default; their counts are
        subtracted from ``total`` as well.
        """

        params = _stats_params(start=start, end=end, include_paths=include_paths)
        params["limit"] = limit
        if group is not None:
            params["group"] = group

        if exclude_paths:
            params["exclude_paths"] = exclude_paths

        data = await self._request("/stats/hits", params=params)

        if exclude_events and isinstance(data, dict):
            _remove_event_hits(data)

        return data

    async def get_stats_page(
        self,
        page: str,
        *,
        start: str | None = None,
        end: str | None = None,
        limit: int = 20,
        offset: int | None = None,
        include_paths: list[int] | None = None,
    ) -> dict[str, Any]:
        """Get one of GoatCounter's breakdown statistics pages."""

        params = _stats_params(start=start, end=end, include_paths=include_paths)
        params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        return await self._request(f"/stats/{page}", params=params)


def _remove_events_from_total(data: dict[str, Any]) -> None:
    """Make ``total`` count only pageviews, keeping the event count separate."""

    total = data.get("total")
    total_events = data.get("total_events")

    if isinstance(total, int) and isinstance(total_events, int):
        data["total"] = max(total - total_events, 0)


def _remove_event_hits(data: dict[str, Any]) -> None:
    """Drop event rows and adjust the response total to match."""

    hits = data.get("hits")
    if not isinstance(hits, list):
        return

    event_hits = [hit for hit in hits if hit.get("event")]
    if not event_hits:
        return

    data["hits"] = [hit for hit in hits if not hit.get("event")]

    total = data.get("total")
    removed = sum(hit.get("count", 0) for hit in event_hits)
    if isinstance(total, int) and isinstance(removed, int):
        data["total"] = max(total - removed, 0)


def _normalize_time(value: str, *, end: bool) -> str:
    """Normalize user dates to the RFC 3339 timestamps GoatCounter accepts.

    Date-only values are treated as whole days, so an ``end`` of ``2026-10-28``
    becomes the end of that day rather than midnight at its start.
    """

    text = value.strip()

    try:
        day = date.fromisoformat(text)
    except ValueError:
        day = None

    if day is not None:
        timestamp = datetime.combine(
            day,
            time(23, 59, 59) if end else time(0, 0, 0),
            tzinfo=timezone.utc,
        )
        return _format_utc(timestamp)

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        # Leave unknown values untouched so the API reports them.
        return value

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return _format_utc(parsed)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stats_params(
    *,
    start: str | None,
    end: str | None,
    include_paths: list[int] | None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    if start:
        params["start"] = _normalize_time(start, end=False)

    if end:
        params["end"] = _normalize_time(end, end=True)

    if include_paths:
        params["include_paths"] = include_paths

    return params


def _retry_delay(headers: httpx.Headers, attempt: int) -> float:
    reset = headers.get("X-Rate-Limit-Reset")
    if reset:
        try:
            return max(float(reset), 0.0) + 0.5
        except ValueError:
            pass

    retry_after = headers.get("Retry-After")
    if retry_after:
        try:
            return max(float(retry_after), 0.0)
        except ValueError:
            pass

    backoff = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))

    return min(backoff, MAX_BACKOFF_SECONDS) + random.uniform(0, 0.25)


def _error_from_response(response: httpx.Response) -> GoatcounterAPIError:
    detail = ""

    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, dict):
        error = payload.get("error") or payload.get("Error")
        if isinstance(error, str):
            detail = error
        elif isinstance(payload.get("errors"), dict):
            parts = []
            for key, messages in payload["errors"].items():
                if isinstance(messages, list):
                    parts.append(f"{key}: {', '.join(map(str, messages))}")
                else:
                    parts.append(f"{key}: {messages}")
            detail = "; ".join(parts)

    if not detail:
        detail = response.text[:300].strip() or response.reason_phrase

    return GoatcounterAPIError(
        f"GoatCounter API error (HTTP {response.status_code}): {detail}",
        status_code=response.status_code,
    )
