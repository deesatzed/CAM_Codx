#!/usr/bin/env sh
set -eu
grok inspect
grok --no-auto-update -p "Use CAM to query memory for retry patterns, then summarize sources only." --output-format json
