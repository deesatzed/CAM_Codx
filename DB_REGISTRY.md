# DB_REGISTRY.md — CAM `claw.db` Corpus Registry

**Generated:** 2026-06-29 (from a `/Volumes` sweep)
**Maintained by:** CAM_Codx (program-manager hub)
**Purpose:** Answer at a glance — *which `claw.db` is live, which are backups/experiments,
why each exists, and which are safe to archive.* See `GOAL_CAM_HYGIENE.md` WS3.

## Status legend
- **LIVE** — the active working corpus. Do not move.
- **GANGLION** — engine-managed per-language sibling DB (`instances/<brain>/claw.db`).
- **BACKUP** — older full corpus, fully reproducible / superseded. Archive candidate.
- **EXPERIMENT** — partial/specialized corpus from a specific build or test.
- **EMPTY** — 0-byte or no `methodologies` table. Archive/delete candidate.

## Naming convention (target)
- Live:       `claw.<profile>.live.db`        (e.g. `claw.glm.live.db`)
- Backup:     `claw.<profile>.backup-YYYYMMDD-HHMMSS.db`
- Experiment: `claw.<profile>.exp-<slug>.db`
- Ganglia stay `instances/<brain>/claw.db` (engine-managed; do not rename).

---

## Registry

| Path (`/Volumes/…`) | Methods | Size | Modified | Status | Why it exists / notes |
|---|---:|---:|---|---|---|
| `WS4TB/repo622sn/CAM_CAM/claw.db` | **2474** | 125M | 2026-06-29 | **LIVE** | Active corpus (GLM/Kimi profile). This session's mine+enrich landed here. **Canonical.** |
| `WS4TB/repo622sn/instances/typescript/claw.db` | 57 | 4.8M | 2026-06-29 | GANGLION | TS brain sibling of the live corpus. |
| `WS4TB/repo622sn/instances/rust/claw.db` | 18 | 3.8M | 2026-06-29 | GANGLION | Rust brain sibling of the live corpus. |
| `WS4TB/ccxt/claw.db` | 2315 | 125M | 2026-06-25 | BACKUP | Recent full corpus from ccxt work; near-live size. Verify before archive. |
| `WS4TB/ccxt/data/claw.db` | 2315 | 109M | 2026-06-25 | BACKUP | Duplicate of above under `data/`. |
| `WS4TB/ccxt/instances/typescript/claw.db` | 31 | 3.1M | 2026-06-25 | GANGLION | ccxt TS ganglion. |
| `WS4TB/instances/typescript/claw.db` | 31 | 3.7M | 2026-06-25 | GANGLION | Orphaned TS ganglion at WS4TB root (no parent corpus alongside). |
| `WS4TB/camcxBU64/CAM_CAM/data/claw.db` | 2427 | 123M | 2026-06-18 | BACKUP | Largest non-live corpus; the "backup ahead of canonical" noted in RISK_NOTES. |
| `WS4TB/camcxBU64/codex-cam-methodology-impl/data/claw.db` | 603 | 27M | 2026-06-04 | EXPERIMENT | Codex methodology-impl build. |
| `WS4TB/camcxBU64/data/claw.db` | 96 | 3.8M | 2026-06-04 | EXPERIMENT | Small starter/seed corpus. |
| `WS4TB/buccx623/CAM_CAM/claw.db` | 2304 | 109M | 2026-06-23 | BACKUP | Full corpus from buccx623 checkout. |
| `WS4TB/careframe/claw.db` | 2304 | 109M | 2026-06-21 | BACKUP | Full corpus in careframe work dir. |
| `WS4TB/careframe/data/claw.db` | 95 | 4.6M | 2026-06-20 | EXPERIMENT | Small corpus under careframe/data. |
| `WS4TB/careframe/instances/typescript/claw.db` | 12 | 3.8M | 2026-06-20 | GANGLION | careframe TS ganglion. |
| `WS4TB/CAM_Locl/data/claw.db` | 2280 | 107M | 2026-06-07 | BACKUP | CAM_Locl full corpus. |
| `WS4TB/WS4TBr/CAM-Pulse/data/claw.db` | 1102 | 47M | 2026-05-04 | EXPERIMENT | CAM-Pulse era corpus (older lineage). |
| `WS4TB/_MyGhRepos/CAM_CAM/data/claw.db` | 107 | 4.5M | 2026-05-17 | EXPERIMENT | Small GH-repos corpus. |
| `WS4TB/CAM_grok_build/CAM_Codx/data/claw.db` | 96 | 3.8M | 2026-05-29 | EXPERIMENT | Grok build seed corpus. |
| `WS4TB/WS4TBr/CAM_Codx/data/claw.db` | 96 | 4.6M | 2026-05-28 | EXPERIMENT | CAM_Codx seed corpus. |
| `WS4TB/repo421sn/data/claw.db` | 34 | 800K | 2026-04-06 | EXPERIMENT | Early small corpus. |
| `WS4TB/repo421sn/book-to-screenplay/data/claw.db` | 0 | 448K | 2026-03-24 | EMPTY | 0 methodologies. Delete candidate. |
| `WS4TB/WS4TBr/a_aSatzClaw/cam-backup-20260328T124226/claw.db` | — | 0B | 2026-03-24 | EMPTY | 0-byte. Delete candidate. |
| `WS4TB/WS4TBr/a_aSatzClaw/cam-backup-20260328T150350/claw.db` | — | 0B | 2026-03-24 | EMPTY | 0-byte. Delete candidate. |
| `WS4TB/WS4TBr/a_aSatzClaw/multiclaw/claw.db` | — | 0B | 2026-04-06 | EMPTY | 0-byte. (multiclaw siblings referenced by stale claw.toml.) |
| `WS4TB/WS4TBr/CAM_CAM/CAM-Pulse/claw.db` | — | 0B | 2026-05-05 | EMPTY | 0-byte. Delete candidate. |
| `WS4TB/WS4TBr/CAMbuMain327/multiclaw/claw.db` | — | 0B | 2026-03-27 | EMPTY | 0-byte. Delete candidate. |
| `WS4TB/WS4TBr/clawDBA/claw.db` | — | 0B | 2026-04-10 | EMPTY | 0-byte. Delete candidate. |
| `WS4TB/WS4TBr/imb-CAM/multiclaw/claw.db` | — | 0B | 2026-04-01 | EMPTY | 0-byte. Delete candidate. |
| `WS4TB/WS4TBr/RNACAM/clawDBA/claw.db` | — | 0B | 2026-04-11 | EMPTY | 0-byte. Delete candidate. |

(Plus local backups in the live dir: `repo622sn/CAM_CAM/claw.db.bak-20260629-062002`,
`claw.db.bak-enrich-20260629-065251` — pre-mine and pre-enrich snapshots from 2026-06-29.)

---

## Summary

- **1 LIVE** corpus (repo622sn/CAM_CAM, 2474) + its 2 ganglia.
- **6 BACKUP** full corpora (2280–2427 methods) — candidates to consolidate/archive.
- **7 EXPERIMENT** partial corpora (34–1102).
- **6 GANGLION** sibling DBs (some orphaned).
- **8 EMPTY** (0-byte / no table) — safe delete candidates.

## Retention policy (proposed)
- Keep LIVE + its ganglia always.
- Keep the single largest BACKUP (`camcxBU64`, 2427) as the cold spare; archive the rest.
- EMPTY DBs: delete after confirming no config references them (note: `multiclaw/*` are
  referenced by stale `claw.toml` siblings — now disabled, see WS4).
- Re-verify this registry whenever a mine/enrich runs against a new path.
