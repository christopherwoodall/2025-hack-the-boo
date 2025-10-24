#!/usr/bin/env python3
"""
Agent Manager for Gemini CLI
Manages agent templates and renders them to GEMINI.md
"""

import json
import shutil
from pathlib import Path
from typing import Optional


class AgentManager:
    """Manages agent templates for Gemini CLI."""
    AGENT_FILE_SUFFIX = "*_agent.md"

    def __init__(
        self,
        templates_dir: Optional[Path] = None,
        gemini_dir: Optional[Path] = None
    ):
        self.templates_dir = templates_dir or (Path(__file__).parent / "templates")
        self.gemini_dir = gemini_dir or (Path.home() / ".gemini")
        self.output_file = self.gemini_dir / "GEMINI.md"
    
    def list_agents(self) -> list[tuple[str, str]]:
        """
        List all available agent templates.
        
        Returns:
            list of (agent_name, description) tuples
        """
        agents = []
        
        if not self.templates_dir.exists():
            return agents

        for template_file in sorted(self.templates_dir.glob(self.AGENT_FILE_SUFFIX)):
            agent_name = template_file.stem
            
            # Try to extract description from first line
            description = ""
            try:
                with open(template_file, 'r') as f:
                    first_line = f.readline().strip()
                    # Check if it's a comment with description
                    if first_line.startswith("<!--") and "DESCRIPTION:" in first_line:
                        description = first_line.split("DESCRIPTION:", 1)[1].split("-->")[0].strip()
            except Exception:
                pass
            
            agents.append((agent_name, description))
        
        return agents
    
    def get_current_agent(self) -> Optional[str]:
        """
        Get the currently active agent by reading GEMINI.md metadata.
        
        Returns:
            Agent name or None if not set
        """
        if not self.output_file.exists():
            return None
        
        try:
            with open(self.output_file, 'r') as f:
                first_line = f.readline().strip()
                # Look for metadata comment: <!-- AGENT: name -->
                if first_line.startswith("<!--") and "AGENT:" in first_line:
                    agent = first_line.split("AGENT:", 1)[1].split("-->")[0].strip()
                    return agent
        except Exception:
            pass
        
        return None
    
    def switch_agent(self, agent_name: str, dry_run: bool = False) -> bool:
        """
        Switch to a different agent template.
        
        Args:
            agent_name: Name of the agent (without .md extension)
            dry_run: If True, show what would be done without making changes
        
        Returns:
            bool: True if successful, False otherwise
        """
        template_file = self.templates_dir / f"{agent_name}.md"
        
        if not template_file.exists():
            print(f"Error: Agent template '{agent_name}' not found at {template_file}")
            return False
        
        # Read template
        try:
            with open(template_file, 'r') as f:
                template_content = f.read()
        except Exception as e:
            print(f"Error reading template: {e}")
            return False
        
        # Add metadata comment to track current agent
        output_content = f"<!-- AGENT: {agent_name} -->\n{template_content}"
        
        if dry_run:
            print(f"Would switch to agent: {agent_name}")
            print(f"Would write to: {self.output_file}")
            print("\nPreview:")
            print("-" * 60)
            print(output_content[:500])
            if len(output_content) > 500:
                print("...")
            return True
        
        # Create .gemini directory if it doesn't exist
        self.gemini_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup existing GEMINI.md if it exists
        if self.output_file.exists():
            backup_file = self.output_file.with_suffix('.md.backup')
            shutil.copy2(self.output_file, backup_file)
            print(f"Backed up existing GEMINI.md to {backup_file}")
        
        # Write new content
        try:
            with open(self.output_file, 'w') as f:
                f.write(output_content)
            print(f"✓ Switched to agent: {agent_name}")
            print(f"✓ Updated: {self.output_file}")
            return True
        except Exception as e:
            print(f"Error writing GEMINI.md: {e}")
            return False
    
    def show_agent(self, agent_name: str) -> bool:
        """
        Display the contents of an agent template.
        
        Args:
            agent_name: Name of the agent (without .md extension)
        
        Returns:
            bool: True if successful, False otherwise
        """
        template_file = self.templates_dir / f"{agent_name}.md"
        
        if not template_file.exists():
            print(f"Error: Agent template '{agent_name}' not found")
            return False
        
        try:
            with open(template_file, 'r') as f:
                content = f.read()
            print(content)
            return True
        except Exception as e:
            print(f"Error reading template: {e}")
            return False
    
    def create_template(self, agent_name: str, description: str = "") -> bool:
        """
        Create a new agent template.
        
        Args:
            agent_name: Name for the new agent
            description: Optional description
        
        Returns:
            bool: True if successful, False otherwise
        """
        template_file = self.templates_dir / f"{agent_name}.md"
        
        if template_file.exists():
            print(f"Error: Agent template '{agent_name}' already exists")
            return False
        
        # Create templates directory if it doesn't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Create template content
        content = f"""<!-- DESCRIPTION: {description or f"Agent template for {agent_name}"} -->

# {agent_name.replace('_', ' ').title()} Agent

You are an AI assistant specialized in {agent_name.replace('_', ' ')}.

## Your Role

[Describe the agent's role and capabilities]

## Available Tools

[List the MCP tools this agent should use]

## Guidelines

[Provide specific guidelines for this agent]

## Example Workflows

[Show example interactions or workflows]
"""
        
        try:
            with open(template_file, 'w') as f:
                f.write(content)
            print(f"✓ Created agent template: {template_file}")
            print(f"\nEdit the template at: {template_file}")
            print(f"Then activate it with: agent-manager switch {agent_name}")
            return True
        except Exception as e:
            print(f"Error creating template: {e}")
            return False


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Manage Gemini CLI agent templates"
    )
    
    parser.add_argument(
        "--templates-dir",
        type=Path,
        help="Path to templates directory (default: agents/)",
        default=Path(__file__).parent.parent / "agents"
    )
    
    parser.add_argument(
        "--gemini-dir",
        type=Path,
        help="Path to .gemini directory (default: .gemini/)",
        default=Path(__file__).parent.parent / ".gemini/"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List command
    subparsers.add_parser(
        "list",
        help="List all available agent templates"
    )
    
    # Current command
    subparsers.add_parser(
        "current",
        help="Show currently active agent"
    )
    
    # Switch command
    switch_parser = subparsers.add_parser(
        "switch",
        help="Switch to a different agent"
    )
    switch_parser.add_argument(
        "agent_name",
        help="Name of the agent to switch to"
    )
    switch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    # Show command
    show_parser = subparsers.add_parser(
        "show",
        help="Display an agent template"
    )
    show_parser.add_argument(
        "agent_name",
        help="Name of the agent to show"
    )
    
    # Create command
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new agent template"
    )
    create_parser.add_argument(
        "agent_name",
        help="Name for the new agent"
    )
    create_parser.add_argument(
        "--description",
        help="Description of the agent"
    )
    
    args = parser.parse_args()
    
    # Create manager
    manager = AgentManager(
        templates_dir=args.templates_dir,
        gemini_dir=args.gemini_dir
    )
    
    if args.command == "list":
        agents = manager.list_agents()
        if not agents:
            print("No agent templates found")
            print(f"\nCreate one with: agent-manager create <name>")
            return
        
        current = manager.get_current_agent()
        print(f"Available agents ({len(agents)}):\n")
        
        for name, description in agents:
            marker = " (active)" if name == current else ""
            print(f"  • {name}{marker}")
            if description:
                print(f"    {description}")
            print()
    
    elif args.command == "current":
        current = manager.get_current_agent()
        if current:
            print(f"Current agent: {current}")
        else:
            print("No agent currently active")
    
    elif args.command == "switch":
        manager.switch_agent(args.agent_name, dry_run=args.dry_run)
    
    elif args.command == "show":
        manager.show_agent(args.agent_name)
    
    elif args.command == "create":
        manager.create_template(args.agent_name, args.description or "")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()