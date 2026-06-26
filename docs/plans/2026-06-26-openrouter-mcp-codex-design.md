# OpenRouter MCP For Codex Design

## Goal

Make OpenRouter available to Codex in the least misleading way:

- use OpenRouter's hosted MCP server for live model/catalog/price/credit/probe tools;
- avoid treating MCP registration as a Codex model-provider registration;
- define a separate bridge path if the experiment needs OpenRouter models to act as child coding agents.

## Current Findings

Codex supports MCP management locally:

```bash
codex mcp add <name> --url <URL>
codex mcp login <name>
codex mcp get <name>
```

OpenRouter documents a hosted MCP server at:

```text
https://mcp.openrouter.ai/mcp
```

That server is OAuth-based and exposes live OpenRouter tools such as model search, model details, endpoint/provider metadata, rankings, credits, benchmarks, docs search, and a billable `chat-send` test tool.

The XTtape product-gap runner previously failed when it tried:

```bash
codex exec -c 'model_provider="openrouter"'
```

That failure is a Codex model-provider configuration problem. Registering an MCP server does not automatically turn OpenRouter into a Codex model backend.

## Recommended Architecture

### Layer 1: Hosted OpenRouter MCP

Register OpenRouter's official hosted MCP server with Codex:

```bash
codex mcp add openrouter --url https://mcp.openrouter.ai/mcp
codex mcp login openrouter
codex mcp get openrouter
```

Use it inside Codex for:

- verifying exact model slugs;
- checking current model availability and prices;
- checking credits;
- comparing benchmarks;
- sending small prompt probes through `chat-send`.

This is the correct first step because OpenRouter already hosts the MCP server and handles OAuth/key issuance.

### Layer 2: Experiment Harness Integration

Update experiment documentation and scripts so OpenRouter MCP is described as a lookup/probe dependency, not as the execution engine for child Codex sessions.

The harness should fail with a clear diagnostic when `model_provider="openrouter"` is unavailable, instead of implying the app build failed.

### Layer 3: Optional OpenRouter Child Worker

If the experiment needs OpenRouter models to build XTtape apps autonomously, build a separate worker path that calls OpenRouter's Chat Completions API directly.

That worker would:

- read the same `GOAL.md` as Codex arms;
- use `OPENROUTER_API_KEY`;
- call a selected OpenRouter model;
- write files only inside that arm's `app/` directory;
- run the same evaluator scripts;
- record token/cost/generation metadata from OpenRouter.

This is a larger build than MCP registration. It should be treated as a separate implementation task because API-driven coding agents need patch application, command execution boundaries, retry logic, and leakage controls.

## Non-Goals

- Do not build a duplicate OpenRouter MCP server unless the hosted server is unavailable or lacks required tools.
- Do not claim OpenRouter MCP makes Codex itself run on OpenRouter models.
- Do not pass secrets into prompts or generated reports.
- Do not allow OpenRouter worker arms to inspect other arm outputs.

## Acceptance Criteria

- `codex mcp get openrouter` shows an enabled HTTP MCP server.
- OAuth login succeeds or the failure mode is documented.
- XTtape experiment docs distinguish MCP lookup/probing from model-provider execution.
- The OpenRouter child-worker path is either explicitly out of scope or implemented behind a separate command.

