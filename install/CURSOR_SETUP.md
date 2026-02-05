# Connecting Gong MCP Server to Cursor

Yes, you can connect the Gong MCP server to Cursor! Cursor supports MCP servers just like Claude Desktop.

## Quick Setup

### Step 1: Install the Package

If you haven't already, install the Gong MCP server:

**Option A: From source (if you're in the project directory):**
```bash
# Make sure you're in the project directory
cd /Users/dannyzach/Documents/gong-mcp-server

# Install in development mode
pip install -e .

# Or if using uv
uv sync
```

**Option B: Install the wheel file:**
```bash
pip install dist/gong_mcp-0.1.0-py3-none-any.whl
```

### Step 2: Get Your API Keys

You'll need:
1. **Gong Access Key** - From your Gong account settings
2. **Gong Access Key Secret** - From your Gong account settings
3. **Anthropic API Key** (optional) - From [Anthropic Console](https://console.anthropic.com/) - only needed for batch analysis

### Step 3: Configure Cursor

Cursor stores MCP server configuration in its settings. Here's how to set it up:

#### Method 1: Using Cursor Settings UI

1. Open Cursor
2. Press `Cmd+,` (Mac) or `Ctrl+,` (Windows/Linux) to open Settings
3. Search for "MCP" or "Model Context Protocol"
4. Look for MCP server configuration section
5. Add a new server with these settings:
   - **Name**: `gong`
   - **Command**: `gong-mcp`
   - **Environment Variables**:
     - `GONG_ACCESS_KEY`: your_gong_access_key
     - `GONG_ACCESS_KEY_SECRET`: your_gong_access_key_secret
     - `ANTHROPIC_API_KEY`: your_anthropic_key (optional)

#### Method 2: Edit Settings JSON Directly

1. Open Cursor
2. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
3. Type "Preferences: Open User Settings (JSON)"
4. Add this configuration:

```json
{
  "mcp.servers": {
    "gong": {
      "command": "gong-mcp",
      "env": {
        "GONG_ACCESS_KEY": "your_gong_access_key_here",
        "GONG_ACCESS_KEY_SECRET": "your_gong_access_key_secret_here",
        "ANTHROPIC_API_KEY": "your_anthropic_key_here",
        "DIRECT_LLM_TOKEN_LIMIT": "150"
      }
    }
  }
}
```

**Environment Variables:**
- `GONG_ACCESS_KEY` / `GONG_ACCESS_KEY_SECRET`: Required. Your Gong API credentials.
- `ANTHROPIC_API_KEY`: Optional. Required for async batch analysis of large datasets.
- `DIRECT_LLM_TOKEN_LIMIT`: Optional. Token threshold (in K) for direct mode. Default: 150 (150K tokens). Set to 40 for 40K threshold, or 0 to always use direct mode (never call Anthropic API).

#### Method 3: Running from Source (Development)

If you want to run directly from the source code:

```json
{
  "mcp.servers": {
    "gong": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/dannyzach/Documents/gong-mcp-server",
        "run",
        "gong-mcp"
      ],
      "env": {
        "GONG_ACCESS_KEY": "your_gong_access_key_here",
        "GONG_ACCESS_KEY_SECRET": "your_gong_access_key_secret_here",
        "ANTHROPIC_API_KEY": "your_anthropic_key_here",
        "DIRECT_LLM_TOKEN_LIMIT": "150"
      }
    }
  }
}
```

Or using Python directly:

```json
{
  "mcp.servers": {
    "gong": {
      "command": "python",
      "args": [
        "-m",
        "gong_mcp.server"
      ],
      "env": {
        "GONG_ACCESS_KEY": "your_gong_access_key_here",
        "GONG_ACCESS_KEY_SECRET": "your_gong_access_key_secret_here",
        "ANTHROPIC_API_KEY": "your_anthropic_key_here",
        "DIRECT_LLM_TOKEN_LIMIT": "150"
      }
    }
  }
}
```

### Step 4: Restart Cursor

After adding the configuration, completely quit and restart Cursor for the changes to take effect.

## How to Use It

Once connected, you can use the Gong MCP server in Cursor's AI chat. Here are some examples:

### Basic Queries

**List recent calls:**
> "Show me my Gong calls from the last week"

**Get a transcript:**
> "Get the transcript for call ABC123"

**Search by company:**
> "Find all calls with Acme Corp"

**Search by participant email:**
> "Find all calls with john@example.com"

### Analysis Queries

**Analyze recent calls:**
> "Analyze all my calls from January and identify common objections"

**Analyze specific calls:**
> "Analyze these call IDs: [call1, call2, call3] and summarize the key pain points"

**Cross-MCP synthesis** (if you have other MCP servers):
> "What pain points did leads from our Facebook Campaign mention in calls?"

## Cross-MCP Synthesis with HubSpot

**Yes!** The Gong MCP server is specifically designed to work with HubSpot MCP (and other MCP servers) for powerful cross-platform analysis. This is perfect for analysis tasks without any coding.

### How It Works

The Gong MCP server's `search_calls` tool accepts **participant emails** as a parameter. This allows Cursor's AI to:

1. **Get lead emails from HubSpot MCP** (e.g., leads from a specific campaign, deal stage, or company)
2. **Pass those emails to Gong's `search_calls` tool** to find matching calls
3. **Analyze the combined data** to synthesize insights

### Setting Up HubSpot MCP

To use both together, you need to connect HubSpot MCP as well:

1. **Install HubSpot MCP** (if you haven't already)
   - Check the HubSpot MCP documentation for installation instructions
   - Typically: `npm install -g @modelcontextprotocol/server-hubspot` or similar

2. **Add HubSpot to Cursor Settings**

   Add HubSpot alongside Gong in your Cursor settings JSON:

```json
{
  "mcp.servers": {
    "gong": {
      "command": "gong-mcp",
      "env": {
        "GONG_ACCESS_KEY": "your_gong_access_key_here",
        "GONG_ACCESS_KEY_SECRET": "your_gong_access_key_secret_here",
        "ANTHROPIC_API_KEY": "your_anthropic_key_here",
        "DIRECT_LLM_TOKEN_LIMIT": "150"
      }
    },
    "hubspot": {
      "command": "hubspot-mcp",
      "env": {
        "HUBSPOT_API_KEY": "your_hubspot_api_key_here"
      }
    }
  }
}
```

   *(Note: The exact HubSpot MCP command and env vars depend on the HubSpot MCP server you're using - check its documentation)*

3. **Restart Cursor** after adding both servers

### Example Cross-MCP Analysis Queries

Once both are connected, you can ask Cursor to synthesize information between them:

**Campaign Analysis:**
> "What pain points did leads from our Facebook Campaign mention in their Gong calls?"

**Deal Stage Analysis:**
> "Analyze all calls with leads that are in the 'Negotiation' stage in HubSpot and identify common objections"

**Company-Level Insights:**
> "Find all HubSpot contacts from Acme Corp and analyze their Gong call transcripts to identify their main concerns"

**Lead Source Correlation:**
> "Compare the call outcomes for leads from LinkedIn vs. Google Ads - what patterns do you see?"

**Sales Performance:**
> "Get all deals that closed in Q1 from HubSpot, find their associated Gong calls, and analyze what worked in those conversations"

### How Cursor Handles This

When you ask a cross-MCP question, Cursor's AI will:

1. **Use HubSpot MCP tools** to fetch lead/contact data (emails, companies, deal stages, etc.)
2. **Extract email addresses** from the HubSpot results
3. **Call Gong's `search_calls(emails=[...])`** with those emails to find matching calls
4. **Fetch transcripts** for the matching calls
5. **Synthesize the combined data** to answer your question

This all happens automatically - you just ask the question!

### Key Features for Cross-MCP Synthesis

The Gong MCP server includes these features specifically for cross-MCP joins:

- **`search_calls(emails=[...])`** - Match calls by participant emails (the key for joining with HubSpot)
- **`search_calls(domains=[...])`** - Match calls by email domains (useful for company-level analysis)
- **`get_call_participants`** - Lightweight participant lookup for validation
- **Participant metadata** - All call listings include participant emails for easy matching

The AI will automatically use the appropriate tools:
- `list_calls` - List calls in a date range
- `search_calls` - Search by text, emails, or domains
- `get_transcript` - Get full transcript
- `analyze_calls` - Smart analysis (returns directly or starts async job)
- `get_job_status` - Check async job progress
- `get_job_results` - Get completed analysis results

## Available Tools

The Gong MCP server provides these tools:

1. **`list_calls`** - List calls in a date range with participant metadata
2. **`search_calls`** - Search by text query OR participant emails/domains
3. **`get_transcript`** - Get full transcript in text or JSON format
4. **`get_call_participants`** - Lightweight participant lookup
5. **`analyze_calls`** - Smart router that returns transcripts directly OR starts async job
6. **`get_job_status`** - Check async job progress
7. **`get_job_results`** - Get completed analysis results

## Troubleshooting

### "Command not found: gong-mcp"

- Make sure you installed the package: `pip install -e .` or `pip install gong-mcp`
- Verify it's in your PATH: `which gong-mcp` (should show the path)
- Try using the full path or Python module approach (Method 3 above)

### "Module not found" errors

- Make sure Python 3.10 or higher is installed: `python3 --version`
- Reinstall: `pip install --upgrade -e .`

### Cursor doesn't recognize the server

- Make sure you saved the settings file
- Completely quit and restart Cursor (not just reload)
- Check Cursor's MCP server logs/console for errors
- Verify your API keys are correct (no extra spaces)

### Still having issues?

- Check that your API keys are valid
- Try running the server manually to test: `gong-mcp` or `python -m gong_mcp.server`
- Look at Cursor's developer console for error messages

## Testing the Connection

After setup, try asking Cursor:

> "What Gong MCP tools are available?"

Or:

> "List my Gong calls from the last 7 days"

If it works, you'll see the calls listed. If not, check the troubleshooting section above.
