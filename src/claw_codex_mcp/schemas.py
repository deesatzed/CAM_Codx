"""Pydantic v2 input/output models for all 4 MCP tools.

See build_specs.md §3.1–§3.5 for the canonical contract.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CorpusStatus = Literal["connected", "empty", "absent", "degraded"]


# --- Shared provenance envelope (build_specs.md §3 fields table) ---

class MethodologyHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    methodology_id: str = Field(min_length=1, max_length=128)
    name: str = Field(max_length=200)
    source_repo: str
    source_path: str
    source_commit_sha: str | None = None
    mined_at: str
    last_verified_at: str | None = None
    fitness_score: float = Field(ge=0.0, le=1.0)
    fitness_n: int = Field(ge=0)
    domain_tag: str
    stale_bool: bool
    rank_score: float = Field(description="hybrid score; not equal to fitness")
    snippet: str = Field(max_length=240)


# --- cam_recall ---

class CamRecallInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2048)
    k: int = Field(default=5, ge=1, le=20)
    domain_filter: str | None = Field(default=None, max_length=64)
    min_fitness: float = Field(default=0.0, ge=0.0, le=1.0)
    include_embryonic: bool = False
    include_stale: bool = True


class CamRecallOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[MethodologyHit]
    corpus_status: CorpusStatus
    corpus_size: int = Field(default=0, ge=0)
    degraded: bool = False
    reason: str | None = None
    remediation: str | None = None
    query_echo: str


# --- cam_provenance ---

class MethodologyLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: Literal["parent", "child"]
    target_id: str = Field(min_length=1, max_length=128)
    link_type: str
    strength: float


class CamProvenanceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    methodology_id: str = Field(min_length=1, max_length=128)
    include_solution_code: bool = True
    include_links: bool = True


class CamProvenanceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    found: bool
    methodology_id: str
    corpus_status: CorpusStatus
    provenance: MethodologyHit | None = None
    solution_code: str | None = None
    methodology_notes: str | None = None
    files_affected: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    links: list[MethodologyLink] = Field(default_factory=list)
    reason: str | None = None


# --- cam_decisions_search ---

class CamDecisionsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2048)
    k: int = Field(default=5, ge=1, le=20)
    repo_filter: str | None = Field(default=None, max_length=512)
    since_iso: str | None = None


class DecisionHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo: str
    file_path: str
    block_anchor: str
    decided_at: str | None = None
    snippet: str = Field(max_length=320)
    rank_score: float


class CamDecisionsSearchOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[DecisionHit]
    corpus_status: CorpusStatus
    degraded: bool = False
    reason: str | None = None
    index_built_at: str | None = None


# --- cam_record_outcome ---

class CamRecordOutcomeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    methodology_ids: list[str] = Field(min_length=1, max_length=10)
    task_id: str = Field(min_length=1, max_length=128)
    repo: str = Field(min_length=1, max_length=512)
    outcome: Literal["green", "red", "partial", "rejected"]
    evidence: dict[str, Any] = Field(default_factory=dict)
    run_hash: str = Field(min_length=8, max_length=128)
    notes: str | None = Field(default=None, max_length=2048)


class CamRecordOutcomeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recorded: bool
    outcome_id: str | None = None
    duplicate: bool = False
    corpus_status: CorpusStatus
    reason: str | None = None
    ts: str
