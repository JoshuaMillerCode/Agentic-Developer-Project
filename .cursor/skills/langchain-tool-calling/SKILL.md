---
name: langchain-tool-calling
description: Connect LangChain agents to MCP tools for function calling. Use when setting up the LLM agent backend, defining LangChain tools from MCP, structuring prompts for tool use, or wiring the agent to the MCP Server.
---

# LangChain Tool Calling with MCP

## Purpose

The LLM agent backend uses LangChain (or equivalent) to call MCP Server tools in response to user queries. The agent decides when to use which tool and formats the result for the user.

## Architecture

```
User Query  →  LLM Agent  →  (chooses tool)  →  MCP Server  →  External API
                  ↑                                                      │
                  └─────────────── tool result ──────────────────────────┘
```

## Connecting LangChain to MCP

1. **MCP Client**: Use `@modelcontextprotocol/sdk` or LangChain's MCP integration to connect to the MCP Server (stdio or HTTP).
2. **Tool mapping**: Discover MCP tools and convert them to LangChain `StructuredTool` or `@tool` definitions.
3. **Agent**: Bind tools to the LLM; use `create_react_agent`, `AgentExecutor`, or equivalent.

## Tool Definition in LangChain

Each MCP tool becomes a LangChain tool with matching:
- `name`: Same as MCP tool name
- `description`: Same as MCP; this drives when the LLM invokes it
- `args_schema`: Pydantic model or JSON Schema matching MCP `inputSchema`

```python
# Example: wrapping an MCP tool
from langchain_core.tools import tool

@tool
def get_weather(city: str, units: str = "metric") -> str:
    """Fetch current weather for a given city."""
    # Call MCP Server / invoke tool
    ...
```

## Prompt Structure

**System prompt** should:
- Describe the agent's role (e.g., "You help users with weather, jokes, and facts")
- List available tools and when to use each
- Instruct the agent to use tools when relevant and to summarize results clearly

**User prompt**: Pass the user's raw query; the agent decides tool usage.

## Implementation Checklist

- [ ] Connect to MCP Server before starting the agent
- [ ] Map all MCP tools to LangChain tools with correct schemas
- [ ] System prompt clearly describes when to use each tool
- [ ] LLM API key from environment (e.g., `OPENAI_API_KEY`); never hardcode
- [ ] Expose a simple HTTP endpoint (e.g., `/chat`) for the frontend to call

## Error Handling

- If MCP Server is unreachable: return a clear error to the user
- If a tool call fails: surface a user-friendly message; don't expose raw API errors
