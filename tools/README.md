# 🛠️ Tools

## Overview
This directory provides implementations for security tools, MCP servers, and utilities. This document provides an outline of the available tools, how to manage them, and guidelines for creating new MCP servers.

---

## MCP Security Tools
A collection of Model Context Protocol (MCP) servers for common cybersecurity and reverse engineering tools.

## MCP Server Convention
To mark a Python file as an MCP server, include this header comment:
```python
#!/usr/bin/env python3
# MCP-SERVER
# MCP-NAME: tool-name
# MCP-DESCRIPTION: Short description of what this server does
```

## Managing MCP Servers
### Auto-configure all servers:
```bash
# Discover and add new servers
mcp-config update

# Preview changes without applying
mcp-config update --dry-run

# Force update existing servers
mcp-config update --force
```

### List discovered servers:
```bash
mcp-config list
```

### Remove a server:
```bash
mcp-config remove server-name

# Preview removal
mcp-config remove server-name --dry-run
```

### Creating a New MCP Server
1. Create your_tool_server.py in this directory
2. Add the MCP server marker at the top:

```bash
#!/usr/bin/env python3
# MCP-SERVER
# MCP-NAME: your-tool
# MCP-DESCRIPTION: What your tool does
```

3. Implement your server (see `xxd_server.py` as example)
4. Run `mcp-config` update to register it
5. Add entry point to `pyproject.toml` (optional, for convenience):

```toml
[project.scripts]
your-tool-server = "tools.your_tool_server:main"
```

### File Naming Convention
- **MCP Servers:** `*_server.py` with `# MCP-SERVER` marker
- **Helper Scripts:** Any other `.py` files (ignored by auto-discovery)

---

## Useful Tools
A curated list of useful security and analysis tools that can be installed via package managers or manually.

- pwntools
- cyberchef
- tmux
- nmap
- tcpdump
- netcat
- xxd
- binwalk
- gdb
- volatility
- foremost
- exiftool
- sqlmap
- gobuster
- nikto
- hashcat
- John the Ripper
- hydra
- sqlmap
- wireshark
- GTFObins
- hash-identifier(?)
- exploit-db
- linEnum
- linpeas
- Google Maps
- lxc
- shodan
- gpg
- Dcode.fr
