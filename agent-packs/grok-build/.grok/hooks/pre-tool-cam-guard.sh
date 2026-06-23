#!/usr/bin/env sh
# Generated CAM guard hook example. Review before enabling.
case "${GROK_HOOK_EVENT:-}" in
  pre_tool_use)
    case "${GROK_TOOL_NAME:-}" in
      *webhook*|*bridge*|*store_finding*|*promote_recipe*|*queue_mining*)
        echo "CAM mutating or external action requires operator approval" >&2
        exit 1
        ;;
    esac
    ;;
esac
exit 0
