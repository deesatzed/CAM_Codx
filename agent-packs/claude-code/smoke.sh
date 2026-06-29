#!/usr/bin/env sh
set -eu

CONFIG_PATH="${CAM_CLAUDE_MCP_CONFIG:-.mcp.json}"
if [ ! -f "$CONFIG_PATH" ]; then
  echo "Missing $CONFIG_PATH. Copy .mcp.json.example to .mcp.json and replace placeholders first." >&2
  exit 2
fi

claude mcp list
claude --mcp-config "$CONFIG_PATH" -p "Use the configured cam MCP server to call claw_query_memory for retry patterns. Summarize source ids only; do not edit files." --output-format text
