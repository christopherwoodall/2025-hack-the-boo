#!/usr/bin/env python3
# MCP-SERVER
# MCP-NAME: recall
# MCP-DESCRIPTION: Recalls stored text prompts for the agent.
"""
MCP Server for recalling information from markdown files.
- /recall: Lists available prompts.
- /recall <name>: Displays the content of a specific prompt.
"""

import asyncio
from pathlib import Path
from typing import Any, Coroutine, Union

from mcp.server import Server
from mcp.types import TextContent, Tool
import mcp.server.stdio

# --- Constants ---
# The directory where prompt markdown files are stored.
PROMPT_DIR = Path(__file__).parent / "prompts"

# --- Server Initialization ---
server = Server("recall-server")


# -------------------------------
# Utility Functions
# -------------------------------
async def _list_available_prompts() -> str:
    """Scans the PROMPT_DIR and returns a formatted list of available prompts."""
    if not PROMPT_DIR.is_dir():
        return f"Error: Prompt directory not found at '{PROMPT_DIR}'"

    # Find all .md files, get their names without the extension (stem), and lowercase them.
    prompt_files = sorted([p.stem.lower() for p in PROMPT_DIR.glob("*.md")])

    if not prompt_files:
        return "No prompts found."

    # Format the list for display.
    formatted_list = "\n".join(f"- {name}" for name in prompt_files)
    return f"Available prompts:\n{formatted_list}"


async def _get_prompt_content(name: str) -> str:
    """Reads and returns the content of a specific prompt file."""
    # Construct the file path, e.g., "prices" -> "PRICES.md"
    prompt_file = PROMPT_DIR / f"{name.upper()}.md"

    try:
        return prompt_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return f"Error: Prompt '{name}' not found."
    except Exception as e:
        return f"Error reading prompt '{name}': {e}"


# -------------------------------
# Tool Definition
# -------------------------------
@server.list_tools()
async def list_tools() -> list[Tool]:
    """Defines the 'recall_prompt' tool available to the agent."""
    return [
        Tool(
            name="recall_prompt",
            description="Recalls a specific prompt or lists all available prompts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt_name": {
                        "type": "string",
                        "description": "The name of the prompt to recall. If omitted, lists all prompts.",
                    },
                },
            },
        )
    ]


# -------------------------------
# Tool Handler
# -------------------------------
@server.call_tool()
async def call_tool(name: str, args: dict[str, Any]) -> list[TextContent]:
    """Handles incoming calls to the recall tool."""
    if name != "recall_prompt":
        return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]

    # If 'prompt_name' is provided, get its content. Otherwise, list all prompts.
    prompt_name = args.get("prompt_name")
    
    if prompt_name:
        result = await _get_prompt_content(prompt_name)
    else:
        result = await _list_available_prompts()
        
    return [TextContent(type="text", text=result)]


# -------------------------------
# Entry Point
# -------------------------------
async def main():
    """Run the MCP recall server."""
    async with mcp.server.stdio.stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


if __name__ == "__main__":
    try:
        # Ensure the prompt directory exists before starting.
        PROMPT_DIR.mkdir(exist_ok=True)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")