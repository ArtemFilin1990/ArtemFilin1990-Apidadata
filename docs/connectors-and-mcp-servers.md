# Connectors and MCP servers

In addition to tools you make available to the model with function calling, you can give models new capabilities using **connectors** and **remote MCP servers**.

- **Connectors** are OpenAI-maintained MCP wrappers for popular services like Google Workspace or Dropbox.
- **Remote MCP servers** are public MCP servers implementing the Model Context Protocol.

## Quickstart

Both connectors and remote MCP servers are configured through the `mcp` tool type in the Responses API.

### Remote MCP server example

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

### Connector example (Dropbox)

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

## How it works

### 1) Listing available tools

The API fetches server tools and returns an `mcp_list_tools` item.

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

Use `allowed_tools` to limit imported tools and reduce cost/latency.

### 2) Calling tools

When the model invokes a tool, the response includes an `mcp_call` item with call arguments and output.

```json
{
  "type": "mcp_call",
  "name": "roll",
  "arguments": "{\"diceRollExpression\":\"2d4 + 1\"}",
  "output": "4",
  "server_label": "dmcp"
}
```

## Approvals

By default, tool calls require approval. This is surfaced as `mcp_approval_request` and should be answered with `mcp_approval_response`.

For trusted tools, configure `require_approval: "never"` (globally or per tool set) to reduce latency.

## Authentication

Many MCP servers and connectors require OAuth access tokens via the `authorization` field. This token must be supplied on every request because Responses API does not store it.

## Available connectors

- `connector_dropbox`
- `connector_gmail`
- `connector_googlecalendar`
- `connector_googledrive`
- `connector_microsoftteams`
- `connector_outlookcalendar`
- `connector_outlookemail`
- `connector_sharepoint`

## Security notes

- Use trusted MCP servers only.
- Keep approval flow for sensitive actions.
- Validate and log third-party tool data flows.
- Treat URLs returned by tools as untrusted until verified.
- Review retention/residency requirements for each third-party server.

## Usage notes

- Works with Responses, Chat Completions, and Assistants APIs (model/tool compatibility varies by model).
- Tool usage is token-billed; no separate per-call MCP fee.
