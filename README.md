# GoatCounter MCP Server

A stateless [Model Context Protocol](https://modelcontextprotocol.io/) server for
the [GoatCounter](https://www.goatcounter.com/) analytics API. Built with
[FastMCP 4](https://gofastmcp.com/), it speaks MCP `2026-07-28` over Streamable
HTTP and takes credentials from each request, so the server stores no GoatCounter
data.

## Credentials

Send both headers with every request:

| Header | Value |
| --- | --- |
| `X-Goatcounter-URL` | Full instance URL, e.g. `https://stats.example.com` |
| `X-Goatcounter-Token` | GoatCounter API token |

The URL needs `http://` or `https://` and must not include `/api/v0`. The server
reads no GoatCounter environment variables and does not store credentials. Since
credentials travel in HTTP headers, the server runs over HTTP, not STDIO.

## Run

```bash
docker compose up -d
```

Or run the published multi-arch image directly:

```bash
docker run --rm -p 8000:8000 ghcr.io/marcorfilacarreras/goatcounter-mcp-server:latest
```

The MCP endpoint is `http://localhost:8000/mcp`. To build the image locally:

```bash
docker compose up -d --build
```

## Connect

Point your MCP client at the endpoint and add both headers:

```json
{
  "mcpServers": {
    "goatcounter": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "X-Goatcounter-URL": "https://stats.example.com",
        "X-Goatcounter-Token": "your-goatcounter-api-token"
      }
    }
  }
}
```

Create a token in GoatCounter under the user menu → **API**. If your client uses
a different remote-server format, keep the same URL and headers.

## Tools

| Tool | Description |
| --- | --- |
| `get_me` | Current user and token |
| `list_sites` | Accessible sites |
| `list_paths` | Tracked paths (`limit`, `after`) |
| `get_stats_total` | Totals, excluding events (`start`, `end`, `include_paths`, `exclude_events`) |
| `get_stats_hits` | Page stats, excluding event hits (`start`, `end`, `limit`, `group`, `include_paths`, `exclude_paths`, `exclude_events`) |
| `get_stats_refs` | Referrers (`start`, `end`, `limit`, `offset`, `include_paths`) |
| `get_stats_campaigns` | Campaigns (same parameters as referrers) |
| `get_stats_browsers` | Browsers (same parameters as referrers) |
| `get_stats_systems` | Operating systems (same parameters as referrers) |
| `get_stats_sizes` | Screen sizes (same parameters as referrers) |
| `get_stats_locations` | Locations (same parameters as referrers) |

Dates are in UTC and accept `YYYY-MM-DD`, `YYYY-MM-DD HH:MM:SS`, or ISO
timestamps. A date-only `end` includes the whole day. `group` is `hour`, `day`,
`week`, or `month`.

GoatCounter events are not pageviews. `get_stats_total` subtracts the event
count from `total` and reports it separately as `total_events`; `get_stats_hits`
drops event rows. Set `exclude_events` to `false` to receive the raw event-
inclusive results.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pre-commit
pre-commit install
python -m goatcounter_mcp_server
```

The server listens on `http://localhost:8000/mcp`. Run checks with
`pre-commit run --all-files`.

## License

MIT. See [LICENSE](LICENSE) for the copyright notices.
