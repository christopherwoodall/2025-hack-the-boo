#!/usr/bin/env python3
# MCP-SERVER
# MCP-NAME: dig
# MCP-DESCRIPTION: DNS lookup tool for domain information
"""
MCP Server for dig - DNS lookup utility.
Performs forward and reverse DNS lookups asynchronously via subprocess.
"""

import asyncio
import subprocess
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

server = Server("dig-server")


# -------------------------------
# Utility
# -------------------------------
async def run_dig(cmd: list[str], timeout: int = 10) -> str:
    """Run a dig command asynchronously and return its output or error."""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

        if process.returncode != 0:
            return f"Error: {stderr.decode(errors='replace').strip() or 'Unknown error'}"

        return stdout.decode(errors='replace').strip() or "(No output)"
    
    except asyncio.TimeoutError:
        process.kill()
        return f"Error: Query timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


# -------------------------------
# Tool definitions
# -------------------------------
@server.list_tools()
async def list_tools() -> list[Tool]:
    """Define available tools."""
    return [
        Tool(
            name="dns_lookup",
            description="Perform DNS lookup for a domain.",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Domain name to lookup"},
                    "record_type": {
                        "type": "string",
                        "description": "DNS record type (A, AAAA, MX, TXT, NS, CNAME, SOA, ANY)",
                        "enum": ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA", "ANY"],
                        "default": "A",
                    },
                    "nameserver": {
                        "type": "string",
                        "description": "Specific nameserver to query (e.g., 8.8.8.8)",
                    },
                    "short": {
                        "type": "boolean",
                        "description": "Short output (just the answer)",
                        "default": False,
                    },
                },
                "required": ["domain"],
            },
        ),
        Tool(
            name="reverse_dns",
            description="Perform reverse DNS lookup (IP to domain).",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {"type": "string", "description": "IP address to lookup"},
                },
                "required": ["ip"],
            },
        ),
    ]


# -------------------------------
# Tool handler
# -------------------------------
@server.call_tool()
async def call_tool(name: str, args: Any) -> list[TextContent]:
    """Handle incoming tool calls."""
    if name == "dns_lookup":
        domain = args["domain"]
        record_type = args.get("record_type", "A")
        nameserver = args.get("nameserver")
        short = args.get("short", False)

        cmd = ["dig"]
        if short:
            cmd.append("+short")
        if nameserver:
            cmd.append(f"@{nameserver}")
        cmd += [domain, record_type]

    elif name == "reverse_dns":
        ip = args["ip"]
        cmd = ["dig", "+short", "-x", ip]

    else:
        return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]

    result = await run_dig(cmd)
    return [TextContent(type="text", text=result)]


# -------------------------------
# Entry point
# -------------------------------
async def main():
    """Run the MCP dig server."""
    async with mcp.server.stdio.stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user.")
