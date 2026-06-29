import json
import re
from pathlib import Path

from tools import generate_agent_packs


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "agent-packs" / "contract" / "cam_agent_capabilities.json"


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_contract_contains_required_capabilities() -> None:
    contract = _contract()
    capability_ids = {capability["id"] for capability in contract["capabilities"]}

    required = {
        "premine",
        "query_memory",
        "store_finding",
        "verify_claim",
        "request_specialist",
        "export_specialist_exchange",
        "import_specialist_exchange",
        "list_specialist_exchanges",
        "route_agent",
        "escalate",
    }

    assert required <= capability_ids


def test_contract_capability_shape_and_host_subsets() -> None:
    contract = _contract()
    capability_ids = {capability["id"] for capability in contract["capabilities"]}

    for capability in contract["capabilities"]:
        assert capability["id"]
        assert capability["owner_repo"] in {"CAM_CAM", "CAM_Codx"}
        assert capability["surface"] in {"cli", "mcp", "mcp_alias"}
        assert capability["tool_names"]
        assert capability["inputs"]
        assert capability["outputs"]
        assert capability["safety_class"]
        assert isinstance(capability["default_allow"], bool)
        assert isinstance(capability["requires_user_approval"], bool)
        assert capability["source_refs"]

    for host_id, pack in contract["host_packs"].items():
        assert pack["required_files"], host_id
        assert set(pack["supported_capabilities"]) <= capability_ids
        assert pack["verification_commands"], host_id


def test_required_pack_files_exist() -> None:
    contract = _contract()
    for host_id, pack in contract["host_packs"].items():
        host_dir = ROOT / "agent-packs" / host_id
        for required_file in pack["required_files"]:
            assert (host_dir / required_file).is_file(), f"{host_id}/{required_file}"


def test_pack_readmes_use_uniform_setup_and_test_sections() -> None:
    contract = _contract()
    required_sections = [
        "## Quick Start",
        "## Configure CAM MCP",
        "## Verify Discovery",
        "## Smoke Test",
        "## CAM Capabilities",
        "## Safety Policy",
        "## Files",
    ]

    for host_id in contract["host_packs"]:
        readme = (ROOT / "agent-packs" / host_id / "README.md").read_text(encoding="utf-8")
        for section in required_sections:
            assert section in readme, f"{host_id} missing {section}"


def test_every_pack_has_executable_smoke_script() -> None:
    contract = _contract()
    for host_id, pack in contract["host_packs"].items():
        smoke_script = ROOT / "agent-packs" / host_id / "smoke.sh"
        assert "smoke.sh" in pack["required_files"], host_id
        assert smoke_script.is_file(), host_id
        assert smoke_script.stat().st_mode & 0o111, host_id

    assert not (ROOT / "agent-packs" / "grok-build" / "headless-smoke.sh").exists()


def test_landing_page_links_uniform_agent_pack_setup() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required = [
        "Uniform setup and test flow",
        "agent-packs/claude-code/smoke.sh",
        "agent-packs/gemini/smoke.sh",
        "agent-packs/grok-build/smoke.sh",
    ]

    for text in required:
        assert text in readme


def test_generated_files_are_current() -> None:
    contract = generate_agent_packs.load_contract()
    expected_outputs = generate_agent_packs.render_files(contract)

    missing_or_stale = []
    for path, expected in expected_outputs.items():
        if not path.exists():
            missing_or_stale.append(path.relative_to(ROOT))
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected.rstrip() + "\n":
            missing_or_stale.append(path.relative_to(ROOT))

    assert missing_or_stale == []


def test_json_examples_parse() -> None:
    json_paths = [
        ROOT / "agent-packs" / "claude-code" / ".mcp.json.example",
        ROOT / "agent-packs" / "gemini" / "settings.json.example",
    ]
    for path in json_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert "mcpServers" in payload
        assert "cam" in payload["mcpServers"]


def test_pack_files_do_not_contain_real_secret_material() -> None:
    sensitive_patterns = [
        re.compile(r"sk-[A-Za-z0-9]{12,}"),
        re.compile(r"xai-[A-Za-z0-9]{12,}"),
        re.compile(r"AIza[A-Za-z0-9_-]{20,}"),
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        re.compile(r"/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw\.db"),
    ]
    scanned = []
    for path in (ROOT / "agent-packs").rglob("*"):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        scanned.append(path)
        for pattern in sensitive_patterns:
            assert not pattern.search(text), f"{pattern.pattern} in {path}"

    assert scanned
