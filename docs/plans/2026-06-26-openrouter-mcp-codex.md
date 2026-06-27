# OpenRouter MCP For Codex Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Register and verify OpenRouter's hosted MCP server for Codex, then make the XTtape experiment harness honest about the difference between OpenRouter MCP tools and OpenRouter-backed child coding agents.

**Architecture:** Use the hosted OpenRouter MCP server as Codex's live lookup/probe layer. Keep Codex model-provider execution separate; if OpenRouter models must build apps directly, add a dedicated OpenRouter API worker in a later task.

**Tech Stack:** Codex CLI MCP commands, OpenRouter hosted MCP over Streamable HTTP/OAuth, Bash experiment harness, Markdown docs.

---

### Task 1: Register The Hosted OpenRouter MCP

**Files:**
- External config: `$CODEX_HOME/config.toml` or Codex-managed MCP config
- Evidence: `docs/plans/openrouter-mcp-verification.txt`

**Step 1: Check current MCP state**

Run:

```bash
codex mcp list
codex mcp get openrouter
```

Expected: `codex mcp get openrouter` may fail with `No MCP server named 'openrouter' found` before registration.

**Step 2: Register OpenRouter MCP**

Run:

```bash
codex mcp add openrouter --url https://mcp.openrouter.ai/mcp
```

Expected: command exits 0 and adds an HTTP MCP server named `openrouter`.

**Step 3: Authenticate**

Run:

```bash
codex mcp login openrouter
```

Expected: browser OAuth flow opens or Codex prints an auth URL. Complete the OpenRouter consent flow. The generated OpenRouter MCP key is separate from normal API keys and may expire.

**Step 4: Verify registration**

Run:

```bash
codex mcp get openrouter
codex mcp list
```

Expected: `openrouter` appears as enabled, HTTP/streamable transport, OAuth-authenticated or ready to authenticate.

**Step 5: Save evidence**

Create or update:

```text
docs/plans/openrouter-mcp-verification.txt
```

Include:

- date checked;
- exact commands run;
- whether login succeeded;
- any OAuth/manual step needed;
- whether OpenRouter tools appear in a fresh Codex session.

**Step 6: Commit**

Run:

```bash
git add docs/plans/2026-06-26-openrouter-mcp-codex-design.md docs/plans/2026-06-26-openrouter-mcp-codex.md docs/plans/openrouter-mcp-verification.txt
git commit -m "docs: plan OpenRouter MCP integration"
```

Expected: commit contains only the OpenRouter MCP planning/evidence files unless a deliberate harness patch is also included.

### Task 2: Add Honest XTtape Harness Diagnostics

**Files:**
- Modify: `/Volumes/WS4TB/ccxt/xttape-model-ladder/experiments/product-gap/README.md`
- Modify: `/Volumes/WS4TB/ccxt/xttape-model-ladder/experiments/product-gap/scripts/run_all_experiments.sh`
- Evidence: `/Volumes/WS4TB/ccxt/xttape-model-ladder/experiments/product-gap/reports/openrouter_codex_provider_check-<arm>.txt`
- Evidence: `/Volumes/WS4TB/ccxt/xttape-model-ladder/experiments/product-gap/reports/openrouter_codex_provider_check.txt`

**Step 1: Document the distinction**

Update the experiment README to state:

```markdown
OpenRouter MCP provides live lookup/probe tools for Codex. It does not by itself make `codex exec` use OpenRouter as the model provider. OpenRouter child-agent arms require either native Codex provider support or a separate OpenRouter API worker.
```

**Step 2: Add a provider preflight**

In `run_all_experiments.sh`, before launching an OpenRouter arm, run a tiny Codex provider check such as:

```bash
codex exec -C "$ROOT" -m "$model" -c 'model_provider="openrouter"' --ephemeral 'Reply OK.'
```

Capture stdout/stderr to a per-arm evidence file and update a latest pointer:

```text
experiments/product-gap/reports/openrouter_codex_provider_check-<arm>.txt
experiments/product-gap/reports/openrouter_codex_provider_check.txt
```

**Step 3: Block clearly on provider failure**

If the preflight reports `Model provider 'openrouter' not found`, write a blocked result that says:

```text
OpenRouter MCP may be configured, but this Codex build does not expose OpenRouter as a model provider. Use native provider support if available or run the separate OpenRouter API worker. See reports/openrouter_codex_provider_check-<arm>.txt.
```

**Step 4: Dry-run**

Run:

```bash
cd /Volumes/WS4TB/ccxt/xttape-model-ladder
experiments/product-gap/scripts/run_all_experiments.sh --dry-run
```

Expected: dry run lists all arms and does not require `OPENROUTER_API_KEY`.

**Step 5: Run one OpenRouter arm**

Run:

```bash
cd /Volumes/WS4TB/ccxt/xttape-model-ladder
experiments/product-gap/scripts/run_all_experiments.sh --run --only openrouter-deepseek-v4-flash-cam
```

Expected: either the arm launches through native Codex provider support or it blocks with the explicit provider-diagnostic message.

**Step 6: Commit**

Run:

```bash
cd /Volumes/WS4TB/ccxt/xttape-model-ladder
git add experiments/product-gap/README.md experiments/product-gap/scripts/run_all_experiments.sh experiments/product-gap/reports/openrouter_codex_provider_check*.txt
git commit -m "test: clarify OpenRouter provider preflight"
```

Expected: commit is limited to harness diagnostics.

### Task 3: Decide Whether To Build The OpenRouter API Worker

**Files:**
- Create if approved: `/Volumes/WS4TB/ccxt/xttape-model-ladder/experiments/product-gap/scripts/run_openrouter_worker.py`
- Modify if approved: `/Volumes/WS4TB/ccxt/xttape-model-ladder/experiments/product-gap/scripts/run_all_experiments.sh`
- Modify if approved: `/Volumes/WS4TB/ccxt/xttape-model-ladder/experiments/product-gap/README.md`

**Step 1: Write the worker contract**

Create a short spec before coding:

```markdown
The OpenRouter worker reads one arm GOAL.md, calls one selected OpenRouter model, applies only file changes under that arm's app directory, runs the same evaluator, and records OpenRouter generation/cost metadata.
```

**Step 2: Choose execution boundary**

Pick one:

- `proposal-only`: model writes a patch/plan, Codex applies and tests it;
- `autonomous-worker`: worker loops through model calls, patch application, commands, and evaluator retries.

Default recommendation: start with `proposal-only` because it is easier to constrain and compare.

**Step 3: Implement only after approval**

Do not build the worker until the hosted MCP and provider-preflight results prove whether native Codex/OpenRouter execution is unavailable.
