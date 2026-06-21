# Template Guide

CAM_Codx templates are starting points for evidence-bound agent work. They are
not proof that work is complete.

## Goal Templates

- `templates/goals/repo-necromancer-standalone.md`: use when a CAM_CAM packet
  should become a real standalone product repo.
- `templates/goals/cam-repo-audit.md`: use for non-destructive folder and repo
  inventory.
- `templates/goals/cam-generated-product-hardening.md`: use when hardening a
  generated repo while preserving provenance.

## Adapter Templates

- `templates/claude-code/`: bounded handoff prompts and provenance checklists
  for Claude Code.
- `templates/grok-build/`: build briefs and packet checklists for Grok Build.

## Completion Rule

Every template should preserve three facts:

1. Source repos are read-only unless a goal explicitly changes that scope.
2. Packets are evidence, not finished products.
3. Tests, smoke commands, and git status decide whether the work is complete.
