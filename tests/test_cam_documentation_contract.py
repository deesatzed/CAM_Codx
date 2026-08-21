import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _cam_cam_root() -> Path:
    configured = os.environ.get("CAM_CAM_RUNTIME_REPO")
    candidates = [
        Path(configured).expanduser() if configured else None,
        ROOT.parent / "CAM_CAM",
        ROOT.parent / "CAM_CAM_goal3",
    ]
    for candidate in candidates:
        if candidate is not None and (candidate / "README.md").is_file():
            return candidate.resolve()
    raise AssertionError("CAM_CAM documentation checkout could not be resolved")


def test_normal_cam_codx_docs_lead_with_one_outcome_language() -> None:
    documents = [
        ROOT / "README.md",
        ROOT / "docs" / "CAM_CHEATSHEET.md",
        ROOT / "docs" / "CAM_CODEX_PROGRAM_MANAGER.md",
        ROOT / "docs" / "QUICKSTART_CODEX.md",
        ROOT / "docs" / "STATUS.md",
    ]

    for document in documents:
        text = document.read_text(encoding="utf-8")
        assert "Use CAM_Codx to" in text, document
        assert "not yet implemented" not in text.lower(), document
        assert "four specialized" not in text.lower(), document
        assert "cam-codx-swe" not in text, document
        assert "cam-codx-development-brief" not in text, document
        assert "cam-codx-pull-mine-dir" not in text, document


def test_direct_cam_runtime_docs_are_troubleshooting_only_and_do_not_overclaim_chat() -> None:
    cam_cam = _cam_cam_root()
    documents = [
        ROOT / "README.md",
        cam_cam / "README.md",
        cam_cam / "docs" / "CAM_COMMAND_DECISION_TREE.md",
        cam_cam / "docs" / "CAM_OPERATOR_CHEATSHEET.md",
        cam_cam / "docs" / "integrations" / "CAM_CODEX.md",
    ]

    for document in documents:
        text = document.read_text(encoding="utf-8").lower()
        assert "troubleshooting" in text or "runtime development" in text, document
        assert "cam chat is a complete general router" not in text, document
