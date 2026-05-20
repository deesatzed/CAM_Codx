"""Verify the slice fixture is real and contains real data."""

def test_slice_db_has_at_least_10_methodologies(slice_conn) -> None:
    cur = slice_conn.execute("SELECT COUNT(*) FROM methodologies")
    n = cur.fetchone()[0]
    assert n >= 10, f"slice must have >=10 rows; has {n}"


def test_slice_db_methodologies_have_real_provenance(slice_conn) -> None:
    # At least one row in the slice must have populated tags AND populated
    # files_affected. Corpus reality (verified 2026-05-19): in the live claw.db,
    # all viable rows have files_affected = '[]'; only embryonic rows carry
    # real file paths. The slice mixes viable + embryonic so this holds.
    cur = slice_conn.execute(
        "SELECT COUNT(*) FROM methodologies "
        "WHERE tags IS NOT NULL AND tags != '[]' "
        "  AND files_affected IS NOT NULL AND files_affected != '[]'"
    )
    n_with_provenance = cur.fetchone()[0]
    assert n_with_provenance >= 1, (
        f"slice must have >=1 row with populated tags+files_affected; "
        f"found {n_with_provenance}"
    )
