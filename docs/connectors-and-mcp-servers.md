# Connectors and MCP servers

In addition to tools you expose through function calling, the Responses API can use **connectors** and **remote MCP servers** via the built-in `mcp` tool type.

- **Connectors** are OpenAI-maintained integrations (for example: Dropbox, Gmail, Google Drive).
- **Remote MCP servers** are third-party servers on the public Internet implementing the Model Context Protocol (MCP).

> ⚠️ Only connect to trusted servers. Any MCP tool can receive data from your prompt/context and may return untrusted output.

## Quickstart

### Remote MCP server (Responses API)

```bash
curl https://api.openai.com/v1/responses \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $OPENAI_API_KEY" \
-d '{
  "model": "gpt-5",
  "tools": [
    {
      "type": "mcp",
      "server_label": "dmcp",
      "server_description": "A Dungeons and Dragons MCP server to assist with dice rolling.",
      "server_url": "https://dmcp-server.deno.dev/sse",
      "require_approval": "never"
    }
  ],
  "input": "Roll 2d4+1"
}'
```

### Connector (Dropbox)

```bash
curl https://api.openai.com/v1/responses \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $OPENAI_API_KEY" \
-d '{
  "model": "gpt-5",
  "tools": [
    {
      "type": "mcp",
      "server_label": "Dropbox",
      "connector_id": "connector_dropbox",
      "authorization": "<oauth access token>",
      "require_approval": "never"
    }
  ],
  "input": "Summarize the Q2 earnings report."
}'
```

## How MCP tool execution works

### 1) Tool listing phase

On first use, the API fetches available tools from the target server and places an `mcp_list_tools` item in response output.

```json
{
  "type": "mcp_list_tools",
  "server_label": "dmcp",
  "tools": [
    {
      "name": "roll",
      "description": "Given a string of text describing a dice roll..."
    }
  ]
}
```

If you keep this item in conversation context, the platform does not need to re-import tools on every turn.

#### Filtering tools

Use `allowed_tools` to reduce latency/cost and narrow model behavior.

```json
{
  "type": "mcp",
  "server_label": "dmcp",
  "server_url": "https://dmcp-server.deno.dev/sse",
  "allowed_tools": ["roll"]
}
```

### 2) Tool call phase

If the model decides to call a tool, output includes `mcp_call` with arguments and tool output.

```json
{
  "type": "mcp_call",
  "name": "roll",
  "arguments": "{\"diceRollExpression\":\"2d4 + 1\"}",
  "output": "4",
  "server_label": "dmcp"
}
```

## Approval flow

By default, MCP calls require approval.

1. Model requests a call and you receive `mcp_approval_request`.
2. You create the next response with `mcp_approval_response` and `approve: true/false`.

For trusted servers/tools you can lower friction with:

- `"require_approval": "never"` (all tools), or
- selective policy for specific tool names.

## Authentication

Most connectors and many remote MCP servers require OAuth access token via `authorization`.

- Pass token in **every** request where the tool is used.
- Responses API does not persist the authorization token value in returned response objects.

## Available connector IDs

- `connector_dropbox`
- `connector_gmail`
- `connector_googlecalendar`
- `connector_googledrive`
- `connector_microsoftteams`
- `connector_outlookcalendar`
- `connector_outlookemail`
- `connector_sharepoint`

## Security and safety checklist

- Connect only to trusted/official MCP server hosts.
- Keep approvals enabled for sensitive operations.
- Restrict `allowed_tools` to minimum required capabilities.
- Treat URLs and payloads from MCP outputs as untrusted input.
- Log and review data sent to third-party MCP services.
- Validate prompt-injection risk when MCP tools can read external content.
- Check third-party retention/residency policies (important for ZDR/Data Residency requirements).

## Usage notes

- MCP tool support depends on model compatibility.
- Applies across Responses API and related tool-capable APIs.
- Billing is token-based for tool schemas/tool calls; no separate per-call MCP fee in this guide context.
