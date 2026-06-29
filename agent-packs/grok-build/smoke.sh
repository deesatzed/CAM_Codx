#!/usr/bin/env sh
set -eu

CONFIG_PATH="${GROK_CAM_CONFIG:-.grok/config.toml}"
if [ ! -f "$CONFIG_PATH" ]; then
  echo "Missing $CONFIG_PATH. Copy .grok/config.toml.example to .grok/config.toml and replace placeholders first." >&2
  exit 2
fi

grok inspect
grok -p "Use the configured cam MCP server to call claw_query_memory for retry patterns. Summarize source ids only; do not edit files." --output-format json --permission-mode default --disable-web-search
