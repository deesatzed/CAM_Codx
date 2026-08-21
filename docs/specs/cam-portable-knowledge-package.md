# CAM portable knowledge package v1

This specification defines a local, read-only package for moving a bounded CAM
knowledge corpus between trusted machines without moving secrets or silently
changing evidence identity. It supports the CAM Better Evidence Program's E4
and E5 measurements. It is not a database merge, live migration, mining
authorization, or production deployment format.

The machine-readable manifest schema is owned by the benchmark at
`CAM_KnowledgeSourceBench/experiment/portability/manifest.schema.json`.

## Package layout

```text
cam-portable-package/
├── manifest.json
├── state/
│   └── claw.db
└── sources/                 # optional, only when rights/privacy permit
    └── <source-id>/
```

The package contains no executable installer. Consumers copy it into a new
temporary CAM home, verify it, and bind CAM_Codx read-only assessment to the
verified database explicitly. Import into a canonical CAM home is outside v1.

## Required manifest identities

`manifest.json` must validate against schema version 1 and bind:

- a stable package ID and UTC creation time;
- the relative database path, exact SHA-256, byte size, SQLite integrity
  result, CAM schema version, and database privacy classification;
- the immutable CAM_CAM Git revision, Python version, retrieval identity, and
  embedding identity used to create and query the corpus;
- every included source's stable ID, immutable Git revision, license label,
  privacy classification, and relative portable path;
- SHA-256 identities for the source configuration and model profile, recorded
  as metadata only rather than copied configuration files;
- relative path-remapping hints that never embed an original machine's
  absolute path;
- every unavailable source and a non-empty reason;
- a deterministic secret-exclusion attestation with zero findings and an
  explicit `.env` exclusion.

Mutable source labels such as `main` and `latest`, absolute paths, parent-path
escapes, unknown fields, missing integrity results, nonzero secret findings,
and configuration payloads rather than metadata are invalid.

## Build procedure

1. Resolve the exact CAM_CAM checkout, corpus, runtime configuration, model
   profile, retrieval implementation, embedding identity, and source
   revisions. Record hashes before copying.
2. Run `PRAGMA integrity_check` through a read-only SQLite connection. Stop
   unless the result is exactly `ok`.
3. Create a consistent database copy using SQLite's backup mechanism or an
   equivalent transactionally consistent local copy. Never copy a live WAL
   database by selecting only its main file.
4. Include source files only when the manifest's license and privacy boundary
   allows redistribution. Otherwise list the source under
   `unavailable_sources`; retained database evidence must still preserve its
   immutable source identity.
5. Record config/profile hashes and safe identity metadata. Do not copy
   `claw.toml`, model profiles, `.env`, shell state, keychain material, API
   credentials, private keys, provider tokens, or machine-specific secrets.
6. Scan filenames and file contents deterministically. Any secret finding
   fails the package; it cannot be waived by changing the manifest count.
7. Hash the finalized bytes, write `manifest.json`, validate the schema, then
   re-read and verify every declared path and digest.

Private or restricted corpus packaging requires a separate explicit privacy
and transport authorization. Encryption and remote transport are not defined
by v1.

## Install and verification procedure

1. Create a new empty temporary CAM home. Never overlay a canonical or live
   home.
2. Reject symlinks, absolute paths, parent traversal, undeclared files, digest
   drift, database-integrity failure, unsupported runtime/schema identities,
   nonzero secret findings, or ambiguous source revisions.
3. Resolve each path-remapping hint locally. Missing sources remain explicitly
   unavailable; the installer must not fetch, mine, or call a provider.
4. Bind both `CLAW_DB_PATH` and `CAM_CODEX_MCP_DB_PATH` to the verified
   temporary database and use an explicit read-only CAM configuration.
5. Run the preregistered read-only assessment. Compare verdict, evidence IDs,
   provenance, limitations, and unavailable-source warnings with the source
   package receipt.
6. Prove that the package, database, configuration/profile identities, source
   trees, and canonical CAM homes are unchanged after assessment.

Equivalent evidence does not require a source path to exist on the receiving
machine. If a later operation needs unavailable source bytes, CAM_Codx must say
so and recommend an explicit source-inspection or mining phase; it must not
claim sufficiency or silently repair the package.

## Evidence and claims

A portable-package pass proves only that the named corpus and read-only
retrieval behavior survived the tested move with bound identities and no
secret leakage. It does not prove knowledge correctness, improved software,
provider independence for future builds, license rights beyond the recorded
boundary, or production readiness.

E4 must count the original cold mining cost. E5 must report fresh and portable
temporary homes separately and label an unavailable physical MacBook run as
blocked rather than simulated. Only immutable receipts and deterministic
outcome tests may support a portability or reuse claim.
