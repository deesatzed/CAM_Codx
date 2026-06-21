# CAM Repo Audit Goal

## OUTCOME

Produce a non-destructive inventory of a folder containing repos, workspaces,
backups, generated products, and local runtime state.

## PROOF OF DONE

- Every candidate folder is classified as `keep`, `archive_candidate`,
  `delete_candidate`, `needs_user_review`, or `do_not_touch`.
- Git remotes and dirty states are recorded where available.
- The report separates verified evidence from inference.
- No folder is deleted, moved, renamed, archived, or edited.

## SCOPE

Allowed:

- run read-only filesystem and git commands,
- create inventory docs and manifests,
- recommend cleanup order.

Not allowed:

- destructive cleanup,
- opening secrets,
- publishing local-only state.

## ITERATION

1. Find git repos and CAM-like folder names.
2. Record remotes, branches, and dirty status.
3. Identify canonical repos.
4. Classify duplicates and confusing folders.
5. Write the manifest.
6. Verify JSON and report commands.

## COMPLETE

Complete only when cleanup can be discussed from evidence instead of folder
names alone.
