-- Codex-CAM Methodology v1 — outcome log table.
-- Owned exclusively by claw_codex_mcp.tools.record_outcome.
-- Append-only by application code; UNIQUE(run_hash) enforces idempotency.

CREATE TABLE IF NOT EXISTS codex_outcome_log (
    id              TEXT PRIMARY KEY,
    methodology_ids TEXT NOT NULL,
    task_id         TEXT NOT NULL,
    repo            TEXT NOT NULL,
    outcome         TEXT NOT NULL
        CHECK (outcome IN ('green','red','partial','rejected')),
    evidence        TEXT NOT NULL DEFAULT '{}',
    ts              TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    run_hash        TEXT NOT NULL,
    notes           TEXT,
    UNIQUE(run_hash)
);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_ts ON codex_outcome_log(ts DESC);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_repo ON codex_outcome_log(repo);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_outcome ON codex_outcome_log(outcome);
