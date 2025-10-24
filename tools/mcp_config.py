#!/usr/bin/env python3
"""
MCP Configuration Manager
Auto-discovers MCP servers and updates Gemini CLI configuration
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


# Magic comment that identifies MCP servers
MCP_SERVER_MARKER = "# MCP-SERVER"


class MCPConfigManager:
    """Manages MCP server configuration for Gemini CLI."""
    
    def __init__(self, tools_dir: Optional[Path] = None, config_path: Optional[Path] = None):
        self.tools_dir = tools_dir or Path(__file__).parent
        self.config_path = config_path or Path.home() / ".gemini" / "settings.json"
        # Store the project root (parent of tools directory)
        self.project_root = self.tools_dir.parent
    
    def discover_mcp_servers(self) -> dict[str, dict]:
        """
        Discover all MCP servers in the tools directory.
        
        Returns:
            dict: Server name -> server configuration
        """
        servers = {}
        
        # Look for Python files with MCP_SERVER_MARKER
        for file_path in self.tools_dir.glob("*_server.py"):
            if file_path.name.startswith("_"):
                continue
            
            server_info = self._parse_server_file(file_path)
            if server_info:
                servers[server_info["name"]] = server_info["config"]
        
        return servers
    
    def _parse_server_file(self, file_path: Path) -> Optional[dict]:
        """
        Parse a server file to extract MCP configuration.
        
        Returns:
            dict with 'name' and 'config' keys, or None if not an MCP server
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for MCP server marker
            if MCP_SERVER_MARKER not in content:
                return None
            
            # Extract server name from filename
            # e.g., "xxd_server.py" -> "xxd"
            base_name = file_path.stem.replace("_server", "")
            
            # Look for metadata in docstring or comments
            metadata = self._extract_metadata(content)
            
            server_name = metadata.get("name", base_name)
            description = metadata.get("description", f"MCP server for {base_name}")
            
            # Get the relative path from project root
            try:
                relative_path = file_path.relative_to(self.project_root)
            except ValueError:
                # If file is not under project root, use absolute path as fallback
                relative_path = file_path
            
            config = {
                "command": "python",
                "args": [str(relative_path)],
                "description": description,
            }
            
            # Add environment variables if specified
            if "env" in metadata:
                config["env"] = metadata["env"]
            
            return {
                "name": server_name,
                "config": config,
            }
        
        except Exception as e:
            print(f"Warning: Error parsing {file_path}: {e}", file=sys.stderr)
            return None
    
    def _extract_metadata(self, content: str) -> dict:
        """Extract metadata from server file comments/docstring."""
        metadata = {}
        
        # Look for metadata in format: # MCP-NAME: value
        name_match = re.search(r'#\s*MCP-NAME:\s*(.+)', content)
        if name_match:
            metadata["name"] = name_match.group(1).strip()
        
        desc_match = re.search(r'#\s*MCP-DESCRIPTION:\s*(.+)', content)
        if desc_match:
            metadata["description"] = desc_match.group(1).strip()
        
        # Look for environment variables
        env_matches = re.findall(r'#\s*MCP-ENV-(\w+):\s*(.+)', content)
        if env_matches:
            metadata["env"] = {key: value.strip() for key, value in env_matches}
        
        return metadata
    
    def load_config(self) -> dict:
        """Load existing Gemini settings.json."""
        if not self.config_path.exists():
            return {"mcpServers": {}}
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {self.config_path}", file=sys.stderr)
            return {"mcpServers": {}}
    
    def save_config(self, config: dict):
        """Save Gemini settings.json."""
        # Create directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def update_config(self, dry_run: bool = False, force: bool = False) -> dict:
        """
        Update Gemini configuration with discovered servers.
        
        Args:
            dry_run: If True, show what would be done without making changes
            force: If True, overwrite existing server configurations
        
        Returns:
            dict: Statistics about the update
        """
        discovered = self.discover_mcp_servers()
        config = self.load_config()
        
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        stats = {
            "discovered": len(discovered),
            "added": 0,
            "updated": 0,
            "skipped": 0,
        }
        
        for server_name, server_config in discovered.items():
            if server_name in config["mcpServers"]:
                if force:
                    config["mcpServers"][server_name] = server_config
                    stats["updated"] += 1
                    print(f"  Updated: {server_name}")
                else:
                    stats["skipped"] += 1
                    print(f"  Skipped: {server_name} (already exists, use --force to update)")
            else:
                config["mcpServers"][server_name] = server_config
                stats["added"] += 1
                print(f"  Added: {server_name}")
        
        if not dry_run:
            self.save_config(config)
            print(f"\nConfiguration saved to: {self.config_path}")
        else:
            print("\nDry run - no changes made")
        
        return stats
    
    def list_servers(self):
        """List all discovered MCP servers."""
        discovered = self.discover_mcp_servers()
        
        if not discovered:
            print("No MCP servers found in tools directory")
            return
        
        print(f"Found {len(discovered)} MCP server(s):\n")
        
        for name, config in discovered.items():
            print(f"  • {name}")
            if "description" in config:
                print(f"    {config['description']}")
            print(f"    Path: {config['args'][0]}")
            print()
    
    def remove_server(self, server_name: str, dry_run: bool = False) -> bool:
        """Remove a server from configuration."""
        config = self.load_config()
        
        if "mcpServers" not in config or server_name not in config["mcpServers"]:
            print(f"Server '{server_name}' not found in configuration")
            return False
        
        if not dry_run:
            del config["mcpServers"][server_name]
            self.save_config(config)
            print(f"Removed server: {server_name}")
        else:
            print(f"Would remove server: {server_name}")
        
        return True
    
    def clean_duplicates(self, dry_run: bool = False) -> int:
        """
        Remove duplicate server entries (keeps the first occurrence).
        
        Returns:
            int: Number of duplicates removed
        """
        config = self.load_config()
        
        if "mcpServers" not in config:
            print("No servers found in configuration")
            return 0
        
        # Track seen servers and duplicates
        seen = set()
        to_remove = []
        
        # JSON preserves order, so we iterate in order
        for name in list(config["mcpServers"].keys()):
            if name in seen:
                to_remove.append(name)
            else:
                seen.add(name)
        
        if not to_remove:
            print("No duplicate servers found")
            return 0
        
        print(f"Found {len(to_remove)} duplicate(s):")
        for name in to_remove:
            print(f"  - {name}")
        
        if not dry_run:
            # Remove duplicates (removes last occurrences, keeps first)
            for name in to_remove:
                # We need to rebuild dict to remove all but first occurrence
                pass
            
            # Rebuild the mcpServers dict with only unique keys
            new_servers = {}
            for name, conf in config["mcpServers"].items():
                if name not in new_servers:
                    new_servers[name] = conf
            
            config["mcpServers"] = new_servers
            self.save_config(config)
            print(f"\nRemoved {len(to_remove)} duplicate(s)")
        else:
            print("\nDry run - no changes made")
        
        return len(to_remove)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Manage MCP server configuration for Gemini CLI"
    )
    
    parser.add_argument(
        "--tools-dir",
        type=Path,
        help="Path to tools directory (default: ./tools/)",
        default=Path(__file__).parent
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to Gemini settings.json (default: .gemini/settings.json)",
        default=Path(__file__).parent.parent / ".gemini" / "settings.json"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Update command
    update_parser = subparsers.add_parser(
        "update",
        help="Update configuration with discovered servers"
    )
    update_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    update_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing server configurations"
    )
    
    # List command
    subparsers.add_parser(
        "list",
        help="List all discovered MCP servers"
    )
    
    # Remove command
    remove_parser = subparsers.add_parser(
        "remove",
        help="Remove a server from configuration"
    )
    remove_parser.add_argument(
        "server_name",
        help="Name of server to remove"
    )
    remove_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    # Clean command
    clean_parser = subparsers.add_parser(
        "clean",
        help="Remove duplicate server entries"
    )
    clean_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    args = parser.parse_args()
    
    # Create manager
    manager = MCPConfigManager(
        tools_dir=args.tools_dir,
        config_path=args.config
    )
    
    if args.command == "update":
        print("Discovering MCP servers...\n")
        stats = manager.update_config(
            dry_run=args.dry_run,
            force=args.force
        )
        print(f"\nSummary:")
        print(f"  Discovered: {stats['discovered']}")
        print(f"  Added: {stats['added']}")
        print(f"  Updated: {stats['updated']}")
        print(f"  Skipped: {stats['skipped']}")
    
    elif args.command == "list":
        manager.list_servers()
    
    elif args.command == "remove":
        manager.remove_server(args.server_name, dry_run=args.dry_run)
    
    elif args.command == "clean":
        manager.clean_duplicates(dry_run=args.dry_run)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()