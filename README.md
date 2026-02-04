# Gong MCP Server

A Model Context Protocol (MCP) server that exposes Gong call data to Claude with:

- **Smart analysis routing** - Automatically decides whether to return transcripts directly (for inline analysis) or run server-side batch processing (for large datasets)
- **Cross-MCP synthesis** - Join Gong calls with HubSpot leads, Salesforce contacts, or Google Analytics data via email/participant filtering

## Features

### Discovery Tools
- `list_calls` - List calls in a date range with participant metadata
- `search_calls` - Search by text query OR participant emails/domains
- `get_call_participants` - Lightweight participant lookup for join validation

### Content Tools
- `get_transcript` - Get full transcript in text or JSON format

### Analysis Tools (Smart Routing)
- `analyze_calls` - Smart router that returns transcripts directly OR starts async job
- `get_job_status` - Check async job progress
- `get_job_results` - Get completed analysis results

## Installation

### Prerequisites
- **Python 3.10+** (required - the MCP SDK requires Python 3.10 or later)
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Check Python Version

```bash
python3 --version  # Should be 3.10 or higher
```

If you need Python 3.10+, install via:
- macOS: `brew install python@3.12`
- Or use [pyenv](https://github.com/pyenv/pyenv): `pyenv install 3.12`

### Setup

```bash
# Clone or navigate to the project
cd gong-mcp-server

# Option 1: Install with uv (recommended)
uv sync

# Option 2: Create venv with Python 3.10+ and install
python3.12 -m venv venv  # or python3.10, python3.11
source venv/bin/activate
pip install -e .

# Option 3: Install dependencies directly
pip install mcp httpx python-dotenv anthropic
```

### Configuration

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
GONG_ACCESS_KEY=your_gong_access_key
GONG_ACCESS_KEY_SECRET=your_gong_access_key_secret
ANTHROPIC_API_KEY=your_anthropic_api_key  # For batch analysis
```

## Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gong": {
      "command": "uv",
      "args": ["--directory", "/path/to/gong-mcp-server", "run", "gong-mcp"],
      "env": {
        "GONG_ACCESS_KEY": "your_key",
        "GONG_ACCESS_KEY_SECRET": "your_secret",
        "ANTHROPIC_API_KEY": "your_anthropic_key"
      }
    }
  }
}
```

Restart Claude Desktop to load the server.

## Usage Examples

### Basic Queries

**List recent calls:**
> "Show me my Gong calls from the last week"

**Get a transcript:**
> "Get the transcript for call ABC123"

**Search by company:**
> "Find all calls with Acme Corp"

### Cross-MCP Synthesis

When combined with other MCP servers (HubSpot, Salesforce, GA):

> "What pain points did leads from our Facebook Campaign mention in calls?"

Claude will:
1. Get lead emails from HubSpot MCP
2. Pass those emails to `search_calls(emails=[...])`
3. Analyze the matching calls

### Batch Analysis

For large datasets:

> "Analyze all my calls from January and identify common objections"

Claude will:
1. Call `analyze_calls` with the date range
2. Receive `mode=async` with a `job_id`
3. Poll `get_job_status` for progress updates
4. Get results with `get_job_results` when complete

## Smart Routing

The `analyze_calls` tool automatically chooses the best approach:

| Dataset Size | Token Estimate | Mode | What Happens |
|-------------|---------------|------|--------------|
| 3-8 calls | < 150K tokens | `direct` | Transcripts returned for inline analysis |
| 10+ calls | > 150K tokens | `async` | Background job started, poll for results |

The threshold is configurable via `DIRECT_TOKEN_THRESHOLD` environment variable.

## Project Structure

```
gong-mcp-server/
├── pyproject.toml          # Project configuration
├── README.md
├── .env.example
├── src/
│   └── gong_mcp/
│       ├── server.py       # MCP server entry point
│       ├── gong_client.py  # Gong API client
│       ├── tools/          # MCP tool implementations
│       ├── analysis/       # Smart routing & batch processing
│       └── utils/          # Formatters & filters
└── jobs/                   # Job status & results storage
```

## API Reference

### search_calls

Critical for cross-MCP joins:

```python
search_calls(
    query: str = None,        # Text search
    emails: list[str] = None, # Match by participant emails
    domains: list[str] = None,# Match by email domains
    from_date: str = None,
    to_date: str = None,
    limit: int = 50
)
```

### analyze_calls

Smart routing with optional filters:

```python
analyze_calls(
    from_date: str = None,
    to_date: str = None,
    prompt: str = "...",
    call_ids: list[str] = None,  # Specific calls
    emails: list[str] = None,    # Filter by emails
    domains: list[str] = None    # Filter by domains
)
```

## Development

```bash
# Run the server directly
uv run gong-mcp

# Run with Python
python -m gong_mcp.server
```

## License

MIT
