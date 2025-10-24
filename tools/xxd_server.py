#!/usr/bin/env python3
# MCP-SERVER
# MCP-NAME: xxd
# MCP-DESCRIPTION: Hex dump and binary analysis tool
"""
MCP Server for xxd - hex dump utility
Provides hex dump, binary dump, and reverse hex dump capabilities
"""

import asyncio
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Any, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio


class XXDServer:
    """MCP Server for xxd hex dump utility."""
    
    def __init__(self):
        self.server = Server("xxd-server")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="xxd_hex_dump",
                    description="Create a hex dump of data or file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "Input data (text) or file path",
                            },
                            "is_file": {
                                "type": "boolean",
                                "description": "Whether input is a file path",
                                "default": False,
                            },
                            "columns": {
                                "type": "integer",
                                "description": "Number of octets per line (default: 16)",
                                "default": 16,
                            },
                            "length": {
                                "type": "integer",
                                "description": "Number of bytes to dump (default: all)",
                            },
                            "uppercase": {
                                "type": "boolean",
                                "description": "Use uppercase hex letters",
                                "default": False,
                            },
                            "plain": {
                                "type": "boolean",
                                "description": "Plain hex dump without line numbers or ASCII",
                                "default": False,
                            },
                        },
                        "required": ["input"],
                    },
                ),
                Tool(
                    name="xxd_binary_dump",
                    description="Create a binary dump (bits) of data or file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "Input data (text) or file path",
                            },
                            "is_file": {
                                "type": "boolean",
                                "description": "Whether input is a file path",
                                "default": False,
                            },
                            "columns": {
                                "type": "integer",
                                "description": "Number of octets per line (default: 6)",
                                "default": 6,
                            },
                        },
                        "required": ["input"],
                    },
                ),
                Tool(
                    name="xxd_reverse",
                    description="Reverse a hex dump back to binary",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hex_dump": {
                                "type": "string",
                                "description": "Hex dump to reverse",
                            },
                            "output_file": {
                                "type": "string",
                                "description": "Optional output file path",
                            },
                        },
                        "required": ["hex_dump"],
                    },
                ),
                Tool(
                    name="xxd_seek",
                    description="Dump specific portion of file by offset",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to file",
                            },
                            "seek": {
                                "type": "integer",
                                "description": "Offset to start from (in bytes)",
                            },
                            "length": {
                                "type": "integer",
                                "description": "Number of bytes to dump",
                            },
                        },
                        "required": ["file_path", "seek"],
                    },
                ),
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            if name == "xxd_hex_dump":
                return await self._hex_dump(arguments)
            elif name == "xxd_binary_dump":
                return await self._binary_dump(arguments)
            elif name == "xxd_reverse":
                return await self._reverse_dump(arguments)
            elif name == "xxd_seek":
                return await self._seek_dump(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _run_command(
        self,
        cmd: list[str],
        input_data: Optional[bytes] = None,
        timeout: int = 30
    ) -> tuple[str, str, int]:
        """Run a command and return stdout, stderr, returncode."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=subprocess.PIPE if input_data else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data),
                timeout=timeout
            )
            
            return (
                stdout.decode('utf-8', errors='replace'),
                stderr.decode('utf-8', errors='replace'),
                process.returncode
            )
        except asyncio.TimeoutError:
            if process:
                process.kill()
            return "", f"Command timed out after {timeout} seconds", -1
        except Exception as e:
            return "", f"Error executing command: {str(e)}", -1
    
    async def _hex_dump(self, args: dict[str, Any]) -> list[TextContent]:
        """Create a hex dump."""
        input_data = args["input"]
        is_file = args.get("is_file", False)
        columns = args.get("columns", 16)
        length = args.get("length")
        uppercase = args.get("uppercase", False)
        plain = args.get("plain", False)
        
        cmd = ["xxd"]
        
        # Add options
        if columns != 16:
            cmd.extend(["-c", str(columns)])
        
        if length:
            cmd.extend(["-l", str(length)])
        
        if uppercase:
            cmd.append("-u")
        
        if plain:
            cmd.append("-p")
        
        # Handle input
        if is_file:
            # Validate file exists
            if not os.path.exists(input_data):
                return [TextContent(
                    type="text",
                    text=f"Error: File not found: {input_data}"
                )]
            cmd.append(input_data)
            stdout, stderr, returncode = await self._run_command(cmd)
        else:
            # Use stdin for text input
            stdout, stderr, returncode = await self._run_command(
                cmd,
                input_data=input_data.encode('utf-8')
            )
        
        if returncode != 0:
            result = f"Error running xxd:\n{stderr}"
        else:
            result = stdout
        
        return [TextContent(type="text", text=result)]
    
    async def _binary_dump(self, args: dict[str, Any]) -> list[TextContent]:
        """Create a binary (bits) dump."""
        input_data = args["input"]
        is_file = args.get("is_file", False)
        columns = args.get("columns", 6)
        
        cmd = ["xxd", "-b", "-c", str(columns)]
        
        # Handle input
        if is_file:
            if not os.path.exists(input_data):
                return [TextContent(
                    type="text",
                    text=f"Error: File not found: {input_data}"
                )]
            cmd.append(input_data)
            stdout, stderr, returncode = await self._run_command(cmd)
        else:
            stdout, stderr, returncode = await self._run_command(
                cmd,
                input_data=input_data.encode('utf-8')
            )
        
        if returncode != 0:
            result = f"Error running xxd:\n{stderr}"
        else:
            result = stdout
        
        return [TextContent(type="text", text=result)]
    
    async def _reverse_dump(self, args: dict[str, Any]) -> list[TextContent]:
        """Reverse a hex dump back to binary."""
        hex_dump = args["hex_dump"]
        output_file = args.get("output_file")
        
        # Create temporary file for hex dump input
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.hex') as tmp:
            tmp.write(hex_dump)
            tmp_path = tmp.name
        
        try:
            cmd = ["xxd", "-r", tmp_path]
            
            if output_file:
                # Write to output file
                cmd.append(output_file)
                stdout, stderr, returncode = await self._run_command(cmd)
                
                if returncode != 0:
                    result = f"Error reversing hex dump:\n{stderr}"
                else:
                    result = f"Successfully wrote binary data to: {output_file}"
            else:
                # Return as text (be careful with binary data)
                stdout, stderr, returncode = await self._run_command(cmd)
                
                if returncode != 0:
                    result = f"Error reversing hex dump:\n{stderr}"
                else:
                    result = f"Binary output:\n{stdout}\n\n(Note: Binary data may not display correctly as text)"
            
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
        
        return [TextContent(type="text", text=result)]
    
    async def _seek_dump(self, args: dict[str, Any]) -> list[TextContent]:
        """Dump specific portion of file by offset."""
        file_path = args["file_path"]
        seek = args["seek"]
        length = args.get("length")
        
        if not os.path.exists(file_path):
            return [TextContent(
                type="text",
                text=f"Error: File not found: {file_path}"
            )]
        
        cmd = ["xxd", "-s", str(seek)]
        
        if length:
            cmd.extend(["-l", str(length)])
        
        cmd.append(file_path)
        
        stdout, stderr, returncode = await self._run_command(cmd)
        
        if returncode != 0:
            result = f"Error running xxd:\n{stderr}"
        else:
            result = stdout
        
        return [TextContent(type="text", text=result)]
    
    async def run(self):
        """Run the server using stdio transport."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def main():
    """Main entry point."""
    server = XXDServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
