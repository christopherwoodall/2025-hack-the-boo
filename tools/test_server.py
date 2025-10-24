#!/usr/bin/env python3
# MCP-SERVER
# MCP-NAME: test_server
# MCP-DESCRIPTION: Simple test server for MCP
"""
Simple MCP Server for Gemini CLI
Returns a greeting string when called.
"""

import asyncio
import json
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# Create server instance
server = Server("gemini-simple-server")

# Define a simple tool that returns a string
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_greeting",
            description="Returns a simple greeting string",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name to greet (optional)",
                    }
                },
                "required": [],
            },
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    if name == "get_greeting":
        person_name = arguments.get("name", "World")
        greeting = f"Hello, {person_name}! This is a simple MCP server response."
        
        return [
            TextContent(
                type="text",
                text=greeting,
            )
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the server using stdio transport."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )

if __name__ == "__main__":
    asyncio.run(main())