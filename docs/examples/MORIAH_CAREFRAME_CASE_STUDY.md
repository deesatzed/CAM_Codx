# MoriahCareFrame Case Study

MoriahCareFrame is the current proof that the CAM/Codex workflow can produce a
standalone product repo rather than only a packet.

## Evidence

- CAM_CAM Repo Necromancer commit: `40ba9f1 feat: add standalone Repo Necromancer generator`
- MoriahCareFrame product commit: `a82e42c Initial MoriahCareFrame runtime`
- Packet path:
  `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/docs/showpieces/repo_necromancer/moriah_careframe`
- Standalone repo:
  `/Volumes/WS4TB/WS4TBr/MoriahCareFrame`
- GitHub repo:
  `https://github.com/deesatzed/moriahcareframe.git`

## Source Boundary

The earlier packet-only mistake was treating generated evidence under
`docs/showpieces/repo_necromancer/...` as if it were the finished product. The
correct success condition is stronger: the standalone repo path must exist and
contain runtime code, tests, README, provenance docs, and a smoke command.

## Verification Commands

```bash
cd /Volumes/WS4TB/WS4TBr/MoriahCareFrame
PYTHONPATH=src python -m pytest -q
sh scripts/smoke.sh
git diff --check
```

## Lesson

CAM_CAM generates the packet and can scaffold the standalone repo. CAM_Codx
should continue from the generated goal, verify the product repo directly, and
keep source repos read-only unless a later goal changes scope.
