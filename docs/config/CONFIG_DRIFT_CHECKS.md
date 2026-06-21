# Config Drift Checks

These checks compare config shape and scan docs/templates for obvious secret
patterns without printing local secret values.

## TOML Shape Check

```bash
cd /Volumes/WS4TB/repo622sn/CAM_Codx
python - <<'PY'
import tomllib
from pathlib import Path
for path in [
    "/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/claw.toml",
    "templates/config/cam-cam-claw.example.toml",
    "templates/config/adapter-config.example.toml",
]:
    data = tomllib.loads(Path(path).read_text())
    print(path, sorted(data.keys()))
PY
```

## Secret-Pattern Scan

```bash
grep -R "sk-" templates docs || true
grep -R "xai-" templates docs || true
grep -R "AIza" templates docs || true
```

Expected: TOML parses and no real-looking keys appear in docs/templates.
