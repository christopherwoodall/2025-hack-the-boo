# 🤖 Agents

## Instructions

Start the agent in the repository's root directory with `gemini`. If you are not familiar with Gemini, [this](https://www.philschmid.de/gemini-cli-cheatsheet) is a good primer.

A good way to kick an agent off is to use a prompt like this:

```
A new challenge just came in called maximum sound. It's just a wav file. You should do your work in the `./challenges/maximum_sound` directory.
```

---

## Configuration

### Agent System (`agent_manager.py`)
Manages agent "personas" by rendering markdown templates to `.gemini/GEMINI.md`.

**Template Structure**:
- Stored in `agents/*_agent.md`
- First line contains metadata: `<!-- AGENT: agent_name -->`
- Rendered output includes tracking comment: `<!-- DESCRIPTION: ... -->`
- Agent templates must follow the naming pattern: `*_agent.md`

Examples:
- `ctf_solver_agent.md`
- `code_helper_agent.md`
- `web_security_agent.md`

Commands:
```bash
agent-manager list                    # List available agents
agent-manager current                 # Show active agent
agent-manager switch <name>           # Switch agent
agent-manager show <name>             # Display template
agent-manager create <name>           # Create new template
agent-manager switch <name> --dry-run # Preview switch
```

### Example Template (`agents/ctf_solver.md`):
```markdown
<!-- AGENT: ctf_solver -->
<!-- DESCRIPTION: CTF challenge solver with security tool expertise -->

# CTF Solver Agent

You are an expert CTF challenge solver...

## Available Tools
- dig - DNS enumeration
- xxd - Hex dump analysis

## Guidelines
1. Reconnaissance first
2. Document process
3. Look for common patterns
```

---

## Sandboxing

See the [.gemini/sandbox.Dockerfile](/.gemini/sandbox.Dockerfile) for the custom sandbox environment used by the agents. It includes various CTF tools and Python libraries to facilitate challenge solving.

---

## Resources
### Prompting
- https://github.com/anthropics/prompt-eng-interactive-tutorial

### Gemini CLI
- https://github.com/google-gemini/gemini-cli
- https://github.com/google-gemini/gemini-cli/blob/main/docs/get-started/configuration.md
- https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md

### Anthropic
- [Claude Cookbooks](https://github.com/anthropics/claude-cookbooks)
- [Claude Code Skills](https://github.com/anthropics/skills/tree/main/document-skills)
