"""cam_record_outcome handler. The only write path on the MCP surface.

build_specs.md §3.4 + §5.1. Append-only into codex_outcome_log; idempotent
via UNIQUE(run_hash) + INSERT OR IGNORE.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sqlite3
import uuid

from claw_codex_mcp.db import ModeInfo, write_lock
from claw_codex_mcp.schemas import CamRecordOutcomeInput, CamRecordOutcomeOutput

INVOCATION_SCHEMA_VERSION = "codex-cam.invocation.v1"
INVOCATION_EVIDENCE_KEY = "_codex_cam_invocation"

INSERT_SQL = """
INSERT OR IGNORE INTO codex_outcome_log
    (id, methodology_ids, task_id, repo, outcome, evidence, run_hash, notes)
VALUES
    (?, ?, ?, ?, ?, ?, ?, ?)
"""


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _invocation_payload(req: CamRecordOutcomeInput) -> dict[str, object]:
    return {
        "schema_version": INVOCATION_SCHEMA_VERSION,
        "tool": "cam_record_outcome",
        "methodology_ids": sorted(req.methodology_ids),
        "task_id": req.task_id,
        "repo": req.repo,
        "outcome": req.outcome,
        "evidence": req.evidence,
        "run_hash": req.run_hash,
        "notes": req.notes,
    }


def _invocation_digest(req: CamRecordOutcomeInput) -> str:
    payload = _canonical_json(_invocation_payload(req)).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _evidence_with_invocation(req: CamRecordOutcomeInput, digest: str) -> dict[str, object]:
    evidence = dict(req.evidence)
    evidence[INVOCATION_EVIDENCE_KEY] = {
        "schema_version": INVOCATION_SCHEMA_VERSION,
        "tool": "cam_record_outcome",
        "methodology_ids": sorted(req.methodology_ids),
        "task_id": req.task_id,
        "repo": req.repo,
        "outcome": req.outcome,
        "run_hash": req.run_hash,
        "input_digest": digest,
    }
    return evidence


async def handle_record_outcome(
    req: CamRecordOutcomeInput, info: ModeInfo,
) -> CamRecordOutcomeOutput:
    new_id = str(uuid.uuid4())
    invocation_digest = _invocation_digest(req)
    methodology_ids_json = json.dumps(sorted(req.methodology_ids))
    evidence_json = _canonical_json(_evidence_with_invocation(req, invocation_digest))
    ts = _now_iso()

    async with write_lock():
        # uri=True is required so that the connected-mode FK-check can
        # ATTACH DATABASE 'file:...?mode=ro' AS corpus (build_specs.md §5.1).
        # SQLite URI support is a per-connection flag, not global.
        conn = sqlite3.connect(str(info.outcome_db_path), uri=True)
        try:
            conn.execute("PRAGMA busy_timeout = 5000")
            # In connected mode, FK-check the methodology_ids against the corpus.
            if info.mode in ("connected", "degraded") and info.db_path is not None:
                # Attach the corpus DB read-only for FK check.
                conn.execute(
                    f"ATTACH DATABASE 'file:{info.db_path}?mode=ro' AS corpus"
                )
                try:
                    for mid in req.methodology_ids:
                        cur = conn.execute(
                            "SELECT 1 FROM corpus.methodologies WHERE id = ?", (mid,)
                        )
                        if cur.fetchone() is None:
                            return CamRecordOutcomeOutput(
                                recorded=False,
                                corpus_status=info.corpus_status,
                                reason=f"unknown methodology_id: {mid}",
                                ts=ts,
                            )
                finally:
                    conn.execute("DETACH DATABASE corpus")

            cur = conn.execute(
                INSERT_SQL,
                (new_id, methodology_ids_json, req.task_id, req.repo,
                 req.outcome, evidence_json, req.run_hash, req.notes),
            )
            conn.commit()
            if cur.rowcount == 0:
                return CamRecordOutcomeOutput(
                    recorded=False, duplicate=True,
                    corpus_status=info.corpus_status,
                    reason="duplicate run_hash",
                    ts=ts,
                )
            return CamRecordOutcomeOutput(
                recorded=True, outcome_id=new_id, duplicate=False,
                corpus_status=info.corpus_status,
                ts=ts,
            )
        finally:
            conn.close()
