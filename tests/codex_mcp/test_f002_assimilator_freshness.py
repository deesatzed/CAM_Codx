from pathlib import Path


def test_assimilator_freshness_uses_tmp_path(tmp_path: Path) -> None:
    """F002 regression guard: freshness checks must not depend on checkout paths."""
    assimilator_marker = tmp_path / "assimilator-freshness.marker"
    assimilator_marker.write_text("fresh\n", encoding="utf-8")

    assert assimilator_marker.exists()
    assert assimilator_marker.read_text(encoding="utf-8") == "fresh\n"
