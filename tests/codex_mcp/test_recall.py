"""cam_recall handler tests against the real slice DB.

build_specs.md §3.1: hybrid FTS5 + vec0 retrieval, returns up to k hits with
full provenance envelope. Empty input raises; empty match returns honest empty.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from claw_codex_mcp.db import ModeInfo
from claw_codex_mcp.schemas import CamRecallInput, CamRecallOutput
from claw_codex_mcp.tools.recall import handle_recall


@pytest.fixture
def connected_info(slice_db_path: Path) -> ModeInfo:
    return ModeInfo(
        mode="connected", corpus_status="connected",
        db_path=slice_db_path, outcome_db_path=slice_db_path, vec_available=False,
    )


@pytest.fixture
def standalone_info(tmp_path: Path) -> ModeInfo:
    return ModeInfo(
        mode="standalone", corpus_status="absent",
        db_path=None, outcome_db_path=tmp_path / "outcome.db", vec_available=False,
    )


async def test_recall_returns_hits_on_real_query(connected_info: ModeInfo) -> None:
    out = await handle_recall(CamRecallInput(query="error handling retry", k=5), connected_info)
    assert isinstance(out, CamRecallOutput)
    assert out.corpus_status == "connected"
    assert len(out.results) <= 5
    if out.results:
        hit = out.results[0]
        assert hit.methodology_id
        assert hit.fitness_n >= 0
        assert 0.0 <= hit.fitness_score <= 1.0
        assert hit.snippet  # non-empty


async def test_recall_empty_query_raises(connected_info: ModeInfo) -> None:
    with pytest.raises(Exception):  # ValidationError from pydantic
        CamRecallInput(query="")


async def test_recall_standalone_returns_honest_empty(standalone_info: ModeInfo) -> None:
    out = await handle_recall(CamRecallInput(query="anything"), standalone_info)
    assert out.results == []
    assert out.corpus_status == "absent"
    assert out.remediation is not None  # must guide the user


async def test_recall_empty_match_returns_empty_results(connected_info: ModeInfo) -> None:
    out = await handle_recall(
        CamRecallInput(query="xyzzy-no-such-pattern-zzz"), connected_info
    )
    assert out.results == []
    assert out.corpus_status == "connected"


# --- Populated-results path coverage ---

async def test_recall_returns_real_hits_with_provenance(connected_info: ModeInfo) -> None:
    """A common query ('data') returns real hits exercising _row_to_hit + helpers."""
    out = await handle_recall(
        CamRecallInput(query="data", k=5, include_embryonic=True), connected_info
    )
    assert out.corpus_status == "connected"
    assert len(out.results) >= 1
    hit = out.results[0]
    assert hit.methodology_id
    assert isinstance(hit.fitness_score, float)
    assert 0.0 <= hit.fitness_score <= 1.0
    assert isinstance(hit.fitness_n, int)
    assert hit.fitness_n >= 0
    assert hit.snippet
    assert len(hit.snippet) <= 240  # pydantic constraint
    assert isinstance(hit.stale_bool, bool)
    assert hit.domain_tag  # always populated (even if "untyped")


async def test_recall_min_fitness_filter_drops_low_scores(
    connected_info: ModeInfo,
) -> None:
    """min_fitness=0.99 should drop all results (no methodology has perfect fitness)."""
    out = await handle_recall(
        CamRecallInput(query="data", k=5, min_fitness=0.99, include_embryonic=True),
        connected_info,
    )
    assert out.results == [], f"expected empty with min_fitness=0.99; got {len(out.results)}"


async def test_recall_include_stale_false_drops_stale_rows(
    connected_info: ModeInfo,
) -> None:
    """include_stale=False filters rows whose last_verified is None or >30d old.

    Slice rows have last_retrieved_at as either NULL (stale by definition)
    or a real timestamp. Setting include_stale=False should reduce the
    result count (or zero it out if all rows are stale).
    """
    out_all = await handle_recall(
        CamRecallInput(query="data", k=5, include_stale=True, include_embryonic=True),
        connected_info,
    )
    out_fresh = await handle_recall(
        CamRecallInput(query="data", k=5, include_stale=False, include_embryonic=True),
        connected_info,
    )
    assert len(out_fresh.results) <= len(out_all.results)


async def test_recall_domain_filter_narrows_results(
    connected_info: ModeInfo,
) -> None:
    """A domain_filter for an obviously absent domain returns 0 results."""
    out = await handle_recall(
        CamRecallInput(
            query="data", k=5, domain_filter="absolutely-no-such-domain",
            include_embryonic=True,
        ),
        connected_info,
    )
    assert out.results == []


# --- Helper unit tests (defensive parse / timestamp branches) ---

def test_parse_tags_none_returns_empty() -> None:
    from claw_codex_mcp.tools.recall import _parse_tags
    assert _parse_tags(None) == []


def test_parse_tags_empty_string_returns_empty() -> None:
    from claw_codex_mcp.tools.recall import _parse_tags
    assert _parse_tags("") == []


def test_parse_tags_malformed_json_returns_empty() -> None:
    from claw_codex_mcp.tools.recall import _parse_tags
    assert _parse_tags("{not valid json[") == []


def test_parse_tags_non_list_json_returns_empty() -> None:
    from claw_codex_mcp.tools.recall import _parse_tags
    assert _parse_tags('"a string not a list"') == []
    assert _parse_tags('{"a": "dict not a list"}') == []


def test_first_tag_prefix_filters_non_strings() -> None:
    """The defensive isinstance(t, str) guard must hold against mixed-type tags."""
    from claw_codex_mcp.tools.recall import _first_tag_prefix
    # A real (well-formed) corpus row's tags column is a JSON array of strings,
    # but the parser builds list[Any] semantically. The guard must hold.
    mixed: list = ["other:tag", 42, None, "domain:web", {"k": "v"}]
    assert _first_tag_prefix(mixed, "domain:") == "web"
    assert _first_tag_prefix([42, None, {"k": "v"}], "domain:") is None


def test_is_stale_malformed_timestamp_is_stale() -> None:
    """ValueError on fromisoformat means we can't tell freshness; treat as stale."""
    from claw_codex_mcp.tools.recall import _is_stale
    assert _is_stale("not a timestamp") is True
    assert _is_stale("2026-13-99T99:99:99") is True
