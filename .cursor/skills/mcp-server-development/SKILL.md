---
name: mcp-server-development
description: Build MCP (Model Context Protocol) servers that wrap REST APIs. Use when implementing the MCP Server wrapper, defining MCP tools, handling transports (stdio/HTTP), or wrapping third-party API calls.
---

# MCP Server Development

## Purpose

MCP Servers expose external APIs as tools an LLM agent can discover and invoke. For this project, the MCP Server wraps a public REST API (e.g., Weather, Jokes, Facts) and exposes its core operations as MCP tools.

## Architecture

```
LLM Agent Backend  ──▶  MCP Server (this)  ──▶  Public REST API
```

- **Transport**: stdio (for local integration) or HTTP
- **Tools**: Each core API operation becomes one MCP tool
- **Secrets**: API keys via environment variables only; never hardcode

## Tool Definition Pattern

Each tool needs:
- **name**: Lowercase, hyphenated (e.g., `get-weather`)
- **description**: Clear, one-sentence purpose for the LLM to decide when to use it
- **inputSchema**: JSON Schema for parameters (location, units, etc.)

Example tool shape:

```json
{
  "name": "get-weather",
  "description": "Fetch current weather for a given city",
  "inputSchema": {
    "type": "object",
    "properties": {
      "city": { "type": "string", "description": "City name" },
      "units": { "type": "string", "enum": ["metric", "imperial"], "default": "metric" }
    },
    "required": ["city"]
  }
}
```

## Implementation Checklist

- [ ] Read third-party API key from `os.environ` (or equivalent); fail fast if missing
- [ ] One tool per distinct API operation; avoid over-fragmenting
- [ ] Return structured data (e.g., JSON) that the agent can interpret and relay to the user
- [ ] Handle API errors gracefully; return clear error messages, don't crash
- [ ] Document required env vars and how to run the server in README

## File Layout

```
mcp-server/
├── server.py (or index.ts)
├── tools/
│   └── api_tools.py
├── requirements.txt (or package.json)
└── README.md (run instructions, env vars)
```

## Security

- Never log or expose API keys
- Never commit `.env` or files containing secrets
- Add `.env` and `*.env.local` to `.gitignore`
