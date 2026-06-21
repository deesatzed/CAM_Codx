# GitHub-Safe Config Guide

## Rule

Commit examples and templates only. Do not commit local `.env` files, real API
keys, local-only databases, private endpoints, or machine-specific paths.

| Local file | Public/template file | Commit? | Why |
|---|---|---|---|
| `CAM_CAM/claw.toml` | tracked public-safe default plus `templates/config/cam-cam-claw.example.toml` | yes, if sanitized | Currently tracked in `CAM_CAM` as a public runtime default; local overrides and secrets remain uncommitted. |
| `CAM_CAM/claw_cheap.toml` | tracked public-safe default plus `templates/config/cam-cam-claw.example.toml` | yes, if sanitized | Currently tracked in `CAM_CAM` as an alternate public-safe model route. |
| `CAM_CAM/claw_dspro.toml` | tracked public-safe default plus `templates/config/cam-cam-claw.example.toml` | yes, if sanitized | Currently tracked in `CAM_CAM` as a public-safe DeepSeek-oriented route. |
| `CAM_CAM/claw_grok.toml` | tracked public-safe default plus `templates/config/cam-cam-claw.example.toml` | yes, if sanitized | Currently tracked in `CAM_CAM` as a public-safe Grok-oriented route. |
| `CAM_CAM/.env` | never | no | Secrets and local endpoints. |
| `CAM_CAM/.env.example` | link or sanitized example | yes | Onboarding-safe when it contains placeholders. |
| `CAM_CAM/data/claw.db` | never | no | Local runtime database. |
| `.codex/config.toml` | `templates/config/adapter-config.example.toml` | template only | Codex/adapter wiring should not publish local paths. |
| Claude/Grok local adapter config | `templates/config/adapter-config.example.toml` | template only | Adapter docs need placeholders and receipt paths. |

## New User Setup

1. Clone `CAM_Codx` and `CAM_CAM`.
2. Use the tracked `CAM_CAM/claw*.toml` files as public-safe defaults, or copy
   the examples under `templates/config/` to local-only files.
3. Replace placeholders with local paths and API keys.
4. Keep local config ignored and outside commits.
5. Run the drift checks in `docs/config/CONFIG_DRIFT_CHECKS.md`.
