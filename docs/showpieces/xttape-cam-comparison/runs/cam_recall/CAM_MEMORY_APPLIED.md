# CAM_MEMORY_APPLIED.md

## Purpose

This file records the specific CAM context packet items that materially changed the XTtape project brain. The packet was used as methodology guidance only. No app code was copied from mined repositories, and no secrets were exposed.

## Summary Difference

The vanilla XTtape request describes a live AI news ticker with feeds, social signals, summarization, learning, and storage. The CAM recall layer changes the plan by making source integrity, connector governance, idempotent ingestion, receipts, fallback behavior, and evidence gates mandatory from the first implementation phase.

In short: generic XTtape would be a smart ticker. CAM-influenced XTtape is a source-receipted, replayable, auditable ambient intelligence system.

## CAM Items That Materially Changed The Result

| CAM Packet Item | Packet Source Section | Material Change To XTtape |
|---|---|---|
| Config-driven query construction with OR joining | `ai-twitter-bot` | Source/social queries should be explicit config, not hard-coded feed logic. |
| Credential validation at startup with descriptive errors | `ai-twitter-bot` | Connectors must validate required credentials before startup and fail without leaking values. |
| Environment-gated model loading with graceful fallback | `ai-twitter-bot` | AI summarization cannot require a single provider; no-provider fallback is part of the build contract. |
| Graceful degradation with a fallback summarizer | `ai-twitter-bot` | XTtape should still produce limited summaries or status output when AI providers are unavailable. |
| Idempotent duplicate filtering with immediate persistence | `ai-twitter-bot` | Deduplication is now core product logic and a required acceptance test. |
| Structured CLI controls such as dry-run and force flags | `ai-twitter-bot` | Source fetchers need dry-run and replay modes before live ingestion is trusted. |
| Atomic file/data artifact creation checks | `ai-twitter-bot` | Durable source receipts and persisted observations should be written atomically. |
| Safe environment parsing with typed conversion and error handling | `xmcp` | Runtime config validation is a first scaffold requirement. |
| Startup inventory report for loaded tools/connectors | `xmcp` | MCP/source adapters must publish inventory, scopes, and credential status at startup. |
| Conditional debug logging through an environment toggle | `xmcp` | Debugging must be operator-controlled and must not leak credentials. |
| OpenAPI filtering with allow/deny lists and MCP/tool integration patterns | `xmcp` | External source/tool access defaults to read-only allowlists through the MCP boundary. |
| Multi-provider AI model routing with capability detection | `chatbot` | Provider routing must inspect capabilities rather than assume one model path. |
| Tool approval flow with state merging and idempotent persistence | `chatbot` | Any future write-capable social/tool action requires explicit approval and persistence tests. |
| Zod request validation with structured error feedback | `chatbot` | TypeScript-facing service/API contracts should use schema validation and structured errors. |
| Structured application error class with typed error codes | `chatbot` and `prisma-next` | Error envelopes and codes should be designed before connector work. |
| Reasoning UI that opens during streaming and tracks duration | `chatbot` | Source-backed AI explanations should be stateful and inspectable, not just final text. |
| Runtime config validation and normalization | `prisma-next` | Configuration validation is part of definition of done for the first implementation phase. |
| Typed test fixture factories for contract data | `prisma-next` | Tests should use typed fixtures for source, event, receipt, summary, and user-signal records. |
| Auditable cast/escape hatches with explicit reasons | `prisma-next` | Any unsafe integration boundary must be documented with rationale. |
| Opt-in caching via explicit query-plan metadata | `prisma-next` | Caching must be explicit and tied to source identity/freshness, not global magic. |
| Route metadata drives source discovery and radar/rule generation | `RSSHub` | Source adapters should be metadata-rich and support discoverability. |
| Remote configuration loading with error resilience | `RSSHub` | Source configuration can be remote later, but must fail safely and visibly. |
| Ordered middleware chain for request handling | `RSSHub` | Ingestion should have explicit ordering for validation, fetch, normalize, dedupe, persist, summarize, rank. |
| OpenAPI auto-documentation from typed routes | `RSSHub` | Adapter/API contracts should be inspectable by future agents and operators. |
| Deterministic cache keys for route/status APIs | `RSSHub` | Cache keys should include source identity, query, and freshness inputs. |
| Structured request debugging with hit counters | `RSSHub` | Connector health should include observable request and cache behavior. |
| Concurrency tests for request-in-progress behavior | `RSSHub` | Concurrent fetch and duplicate in-flight behavior must be tested before build acceptance. |
| Typed HTTP error class hierarchy | `RSSHub` | External-source errors should be typed and actionable. |
| Browser automation fallback for sources that need scripted access | `RSSHub` | Browser automation is deferred as a fallback lane, not the default ingestion path. |

## Resulting Non-Generic Requirements

- Source adapter inventory and allowlist rules are mandatory.
- Idempotent ingestion and duplicate suppression are first-phase contracts.
- Every summary and ranking decision must retain source receipts.
- Confidence, freshness, and time-decay fields belong in the first data model.
- Typed config validation and structured error envelopes are required before connector work is trusted.
- Model/provider fallback gates are required.
- User-learning data must include reset and retention controls.
- Connector dry-run and replay modes are required.
- Evidence gates must precede any claim that the app build is ready.
- Tests must cover concurrency, duplicate ingestion, tool approval, stale-source behavior, and provider fallback.

## Items Used Only As Guidance

The packet names `ai-twitter-bot`, `xmcp`, `chatbot`, `prisma-next`, and `RSSHub` as mined methodology sources. These names informed patterns and risks only. They do not authorize copying implementation code, secrets, repository structure, or product-specific behavior from those repositories into XTtape.
