# CAM Development Brief

Use the Development Brief when you want one short answer to either of these:

```text
Use cam-codx-development-brief to help me start this new project from relevant prior work.
Use cam-codx-development-brief to decide whether this in-progress repository should continue, be mitigated, or be re-developed.
```

It is for early development and rescue decisions—not another dashboard or a
replacement for engineering judgment.

## What it returns

For a new project, the brief provides relevant prior work, labelled
cross-domain analogies, reusable components/tests/workflows, mistakes to avoid,
and a small starting step.

For an in-progress project, it reads the named target's truth files, Git state,
and visible gap markers, then advises **continue**, **mitigate**, or
**re-develop**. It states the reasons, missing evidence, and smallest safe next
step. It never claims an unrun test passed.

Every recommendation is visibly one of:

- **Direct precedent** — compatible stack/feature evidence.
- **Transferable analogy** — a dissimilar source with its transfer rationale.
- **New hypothesis** — an unproven idea with required validation.

## Safe default

The first run uses only the named target and the explicitly supplied CAM
primary corpus. It does not mine, scan other repositories, contact a provider,
write to `claw.db`, record retrieval telemetry, run target tests, edit code,
create tasks, or change models.

Use the installed skill rather than memorising commands. For an explicit CLI
run, use absolute paths to the CAM_Codx tool, CAM executable, and primary
database:

```bash
python /absolute/path/to/CAM_Codx/tools/development_brief.py new \
  --task "Build a durable import retry flow" \
  --target-repo /absolute/path/to/project \
  --cam-command /absolute/path/to/CAM_CAM/.venv/bin/cam \
  --cam-db /absolute/path/to/CAM_CAM/claw.db
```

Use `continue-rescue` instead of `new` for existing repositories. The brief
prints Markdown by default. Add `--output /explicit/path/brief.md` only when
you want to save it; output inside the target repository is rejected to protect
the read-only default.

## Expanding evidence later

When default-scope evidence is thin, the brief may suggest a scan-only search
of specifically named local folders. Those folders must exist beneath an
explicit approved parent. The brief only renders that later-phase scope; it
does not scan it.

If an active CAM TOML contains sibling database paths that no longer exist, the
brief renders **relocation gate not satisfied** and names the unavailable paths.
It does not broaden retrieval, repair the TOML, or query a sibling corpus.
Mining, provider use, model changes, and self-enhancement remain separate
approval-gated CAM phases.
