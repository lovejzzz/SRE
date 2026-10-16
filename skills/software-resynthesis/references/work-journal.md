# Work records and case reports

When a user requests a full process record, record meaningful decisions, failed
experiments, corrections, verification and remaining limitations as work happens.
Do not reconstruct a success-only narrative at delivery. Keep original full scope
in project.json, even while describing a partial milestone.

`sre.py record WORKSPACE --entry entry.json` creates `journal/<id>.json` without
overwriting. `sre.py report WORKSPACE --out report.md` creates a readable report
and rechecks recorded evidence digests. It returns 1 for evidence drift. These
commands **never** satisfy source-runtime or target acceptance obligations.

Entry format (v1): `schema_version: 1`, `id` (safe filename, max 80 characters), `title`, `objective`,
`outcome` (`progress`, `failed`, `blocked`, `verified`), nonempty `actions` string
array, `difficulties`, `resolutions`, `limitations` string arrays, `result`,
`next_action`, and `evidence` list of `{path, description}`. Evidence paths are
workspace-relative regular files; escapes including symlinks are rejected.
The helper adds UTC `recorded_at` and SHA-256 fingerprints. Evidence is required
for an entry labeled verified. That label describes only the entry's stated work.

Record important commands, exit outcomes, tool/environment versions, elapsed
time when measured, and active owned processes in actions or linked artifacts.
Store immutable snapshots for mutable files so later edits do not destroy the
historical record. Corrections belong in new entries referencing the prior ID.
Hashes do not prevent an author from rewriting both evidence and the record.

Migration: existing workspaces work without reinitialization; record creates a
journal directory on first use. Review and sanitize reports before sharing:
the renderer does not redact paths, private facts or source descriptions.

When a workflow moves from research into implementation, reconcile its feature
status with the code and journal in the same checkpoint. Keep implementation
status separate from acceptance: a runnable first workflow warrants
`implementing`, while missing source comparisons remain explicitly pending.
