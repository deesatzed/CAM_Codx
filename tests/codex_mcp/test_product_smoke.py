from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_product_smoke_cli_runs_all_local_checks(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/product_smoke.py",
            "--work-dir",
            str(tmp_path / "product_smoke"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS version" in result.stdout
    assert "PASS standalone tools" in result.stdout
    assert "PASS standalone recall_absent" in result.stdout
    assert "PASS standalone provenance_absent" in result.stdout
    assert "PASS standalone decisions_search" in result.stdout
    assert "PASS standalone outcome_idempotent" in result.stdout
    assert "PASS connected tools" in result.stdout
    assert "PASS connected recall_real_rows" in result.stdout
    assert "PASS connected provenance_resolves" in result.stdout
    assert "PASS connected decisions_search" in result.stdout
    assert "PASS connected outcome_idempotent" in result.stdout
    assert "PRODUCT SMOKE PASS" in result.stdout
