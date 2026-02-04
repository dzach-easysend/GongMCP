"""
Gong MCP Server

Main entry point for the Gong MCP server.
Exposes Gong call data to Claude with smart analysis routing.
"""

import asyncio
import os

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.calls import list_calls, get_transcript, search_calls
from .tools.participants import get_call_participants
from .tools.analysis import analyze_calls, get_job_status, get_job_results

# Load environment variables
load_dotenv()

# Create MCP server
server = Server("gong-mcp")


# Tool definitions
TOOLS = [
    Tool(
        name="list_calls",
        description=(
            "List Gong calls in a date range. Returns call metadata including "
            "participants with emails (useful for cross-MCP joins)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "from_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format. Defaults to 7 days ago.",
                },
                "to_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format. Defaults to today.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of calls to return. Default 50.",
                    "default": 50,
                },
            },
        },
    ),
    Tool(
        name="get_transcript",
        description="Get the full transcript for a specific Gong call.",
        inputSchema={
            "type": "object",
            "properties": {
                "call_id": {
                    "type": "string",
                    "description": "The Gong call ID.",
                },
                "format": {
                    "type": "string",
                    "enum": ["text", "json"],
                    "description": "Output format. 'text' for readable, 'json' for structured.",
                    "default": "text",
                },
            },
            "required": ["call_id"],
        },
    ),
    Tool(
        name="search_calls",
        description=(
            "Search for calls by text query OR participant emails/domains. "
            "CRITICAL for cross-MCP joins: pass emails from HubSpot/Salesforce to find matching calls."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text search query (searches call titles).",
                },
                "emails": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of participant emails to match. Use for cross-MCP joins.",
                },
                "domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of email domains to match (e.g., ['acme.com']).",
                },
                "from_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format. Defaults to 30 days ago.",
                },
                "to_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format. Defaults to today.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of calls to return. Default 50.",
                    "default": 50,
                },
            },
        },
    ),
    Tool(
        name="get_call_participants",
        description=(
            "Get participant info for multiple calls. Lightweight alternative to fetching "
            "full transcripts. Useful for validating cross-MCP joins."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "call_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of Gong call IDs.",
                },
            },
            "required": ["call_ids"],
        },
    ),
    Tool(
        name="analyze_calls",
        description=(
            "Analyze call transcripts with smart routing. For small datasets (< 150K tokens), "
            "returns transcripts directly for inline analysis. For large datasets, starts an "
            "async job and returns job_id for polling with get_job_status/get_job_results."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "from_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format. Defaults to 7 days ago.",
                },
                "to_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format. Defaults to today.",
                },
                "prompt": {
                    "type": "string",
                    "description": "Analysis prompt/instructions.",
                    "default": "Analyze these call transcripts and extract key insights.",
                },
                "call_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific call IDs to analyze (optional).",
                },
                "emails": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by participant emails (for cross-MCP joins).",
                },
                "domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by email domains.",
                },
            },
        },
    ),
    Tool(
        name="get_job_status",
        description="Check the status of an async analysis job.",
        inputSchema={
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "The job ID from analyze_calls.",
                },
            },
            "required": ["job_id"],
        },
    ),
    Tool(
        name="get_job_results",
        description="Get the results of a completed async analysis job.",
        inputSchema={
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "The job ID from analyze_calls.",
                },
            },
            "required": ["job_id"],
        },
    ),
]


@server.list_tools()
async def handle_list_tools():
    """Return the list of available tools."""
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    import json

    try:
        if name == "list_calls":
            result = await list_calls(
                from_date=arguments.get("from_date"),
                to_date=arguments.get("to_date"),
                limit=arguments.get("limit", 50),
            )

        elif name == "get_transcript":
            result = await get_transcript(
                call_id=arguments["call_id"],
                format=arguments.get("format", "text"),
            )

        elif name == "search_calls":
            result = await search_calls(
                query=arguments.get("query"),
                emails=arguments.get("emails"),
                domains=arguments.get("domains"),
                from_date=arguments.get("from_date"),
                to_date=arguments.get("to_date"),
                limit=arguments.get("limit", 50),
            )

        elif name == "get_call_participants":
            result = await get_call_participants(
                call_ids=arguments["call_ids"],
            )

        elif name == "analyze_calls":
            result = await analyze_calls(
                from_date=arguments.get("from_date"),
                to_date=arguments.get("to_date"),
                prompt=arguments.get(
                    "prompt",
                    "Analyze these call transcripts and extract key insights.",
                ),
                call_ids=arguments.get("call_ids"),
                emails=arguments.get("emails"),
                domains=arguments.get("domains"),
            )

        elif name == "get_job_status":
            result = await get_job_status(
                job_id=arguments["job_id"],
            )

        elif name == "get_job_results":
            result = await get_job_results(
                job_id=arguments["job_id"],
            )

        else:
            result = {"error": f"Unknown tool: {name}"}

        # Return as JSON text content
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        error_result = {"error": str(e), "tool": name}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Main entry point."""
    # Validate configuration
    if not os.getenv("GONG_ACCESS_KEY") or not os.getenv("GONG_ACCESS_KEY_SECRET"):
        print("Warning: GONG_ACCESS_KEY and GONG_ACCESS_KEY_SECRET not configured")

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
