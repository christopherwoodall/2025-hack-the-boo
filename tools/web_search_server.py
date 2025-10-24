#!/usr/bin/env python3
# MCP-SERVER
# MCP-NAME: wenb_search_server
# MCP-DESCRIPTION: An MCP server for performing web searches.
"""
MCP Server for Gemini CLI
Provides a web search tool using DuckDuckGo.
"""

import asyncio
import json
from typing import Any

# Dependencies for the search tool
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

# MCP server components
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio


# Create server instance
server = Server("gemini-search-server")


# This is the core logic from your tool.py, placed here as a helper function.
def _perform_web_search(query: str, max_results: int = 5) -> dict:
    """
    Performs a web search using DuckDuckGo, fetches page content, and returns results.
    """
    try:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=max_results)
        simplified_results = []

        for result in results:
            try:
                # Fetch content from the URL
                response = requests.get(
                    result["href"], headers={"User-Agent": "Mozilla/5.0"}, timeout=10
                )
                response.raise_for_status()

                # Parse and clean the HTML
                soup = BeautifulSoup(response.text, "html.parser")
                for element in soup(["script", "style", "nav", "footer"]):
                    element.decompose() # Remove unwanted tags

                text = soup.get_text(separator=' ', strip=True)
                # Create a concise snippet
                snippet = text[:1000] + "..." if len(text) > 1000 else text

                simplified_results.append(
                    {
                        "title": result.get("title"),
                        "url": result.get("href"),
                        "snippet": snippet, # Use the cleaned, longer snippet
                        "original_description": result.get("body"),
                    }
                )

            except Exception as fetch_err:
                # If fetching the full page fails, use the original DDGS snippet
                simplified_results.append(
                    {
                        "title": result.get("title"),
                        "url": result.get("href"),
                        "snippet": result.get("body"), # Fallback snippet
                        "error": f"Could not fetch full content: {str(fetch_err)}",
                    }
                )

        return {"success": True, "results": simplified_results}

    except Exception as search_err:
        return {"success": False, "error": f"Search failed: {str(search_err)}"}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools. This schema is adapted from your tool.py."""
    return [
        Tool(
            name="web_search_tool",
            description="Search the web using DuckDuckGo and return snippets and page content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find information on the web",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of search results to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle incoming tool calls."""
    if name == "web_search_tool":
        query = arguments.get("query")
        if not query:
            raise ValueError("Missing required argument: 'query'")
        
        max_results = arguments.get("max_results", 5)
        
        # Execute the search
        search_result = _perform_web_search(query=query, max_results=max_results)
        
        # Return the results as a JSON string within a TextContent object
        return [
            TextContent(
                type="text",
                text=json.dumps(search_result, indent=2),
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