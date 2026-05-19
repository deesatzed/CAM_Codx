"""Verify the slice fixture is real and contains real data."""

def test_slice_db_has_at_least_10_methodologies(slice_conn) -> None:
    cur = slice_conn.execute("SELECT COUNT(*) FROM methodologies")
    n = cur.fetchone()[0]
    assert n >= 10, f"slice must have >=10 rows; has {n}"


def test_slice_db_methodologies_have_real_provenance(slice_conn) -> None:
    cur = slice_conn.execute(
        "SELECT tags, files_affected FROM methodologies LIMIT 1"
    )
    tags, files = cur.fetchone()
    assert tags and tags != "[]", "tags must be populated"
    assert files and files != "[]", "files_affected must be populated"
