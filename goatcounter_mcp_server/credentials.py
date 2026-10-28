from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlparse

INSTANCE_URL_HEADER = "x-goatcounter-url"
API_TOKEN_HEADER = "x-goatcounter-token"


class GoatcounterCredentialsError(ValueError):
    """Raised when the request does not contain usable GoatCounter credentials."""


@dataclass(frozen=True, slots=True)
class GoatcounterCredentials:
    """Credentials supplied by a single MCP client request."""

    instance_url: str
    api_token: str

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> GoatcounterCredentials:
        """Build credentials from the current request's HTTP headers."""

        normalized = {name.lower(): value for name, value in headers.items()}

        raw_url = normalized.get(INSTANCE_URL_HEADER, "").strip()
        raw_token = normalized.get(API_TOKEN_HEADER, "").strip()

        if not raw_url:
            raise GoatcounterCredentialsError(
                "Missing X-Goatcounter-URL header. Send the full base URL of your "
                "GoatCounter instance (for example https://stats.example.com) with "
                "every request."
            )

        if not raw_token:
            raise GoatcounterCredentialsError(
                "Missing X-Goatcounter-Token header. Send a GoatCounter API token "
                "with every request."
            )

        return cls(
            instance_url=_normalize_instance_url(raw_url),
            api_token=raw_token,
        )


def _normalize_instance_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)

    if parsed.scheme not in {"http", "https"}:
        raise GoatcounterCredentialsError(
            "X-Goatcounter-URL must be an absolute http:// or https:// URL."
        )

    if not parsed.hostname:
        raise GoatcounterCredentialsError("X-Goatcounter-URL must include a hostname.")

    if parsed.username is not None or parsed.password is not None:
        raise GoatcounterCredentialsError(
            "X-Goatcounter-URL must not contain a username or password. "
            "Send the API token in X-Goatcounter-Token instead."
        )

    if parsed.query or parsed.fragment:
        raise GoatcounterCredentialsError(
            "X-Goatcounter-URL must not contain a query string or fragment."
        )

    path = parsed.path.rstrip("/")
    if path.endswith("/api/v0"):
        raise GoatcounterCredentialsError(
            "X-Goatcounter-URL must be the instance base URL without /api/v0, "
            "for example https://stats.example.com."
        )

    return f"{parsed.scheme}://{parsed.netloc}{path}"
