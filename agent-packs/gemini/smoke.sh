#!/usr/bin/env sh
set -eu

SETTINGS_PATH="${GEMINI_CAM_SETTINGS:-.gemini/settings.json}"
if [ ! -f "$SETTINGS_PATH" ]; then
  echo "Missing $SETTINGS_PATH. Copy settings.json.example to .gemini/settings.json or merge mcpServers.cam first." >&2
  exit 2
fi

gemini mcp list
gemini -p "Use the configured cam MCP server to call claw_query_memory for retry patterns. Summarize source ids only; do not edit files." --allowed-mcp-server-names cam --output-format json
