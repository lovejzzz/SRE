# Project contract and continuity

`sre.py init` creates a new private workspace; it refuses an existing destination. Keep this outside any public repository. It creates:

- `project.json`: schema version, original request, source/target, stage, features, acceptance obligations, decisions, unknowns, and next action.
- `evidence/`: raw observations and source references, kept separate from deliverables.
- `runs/`: normalized traces, comparison reports, logs, environment fingerprints.
- `implementation/`: the successor, with its own build and dependency records.
- `checkpoints/`: concise continuation notes, including owned process/job IDs and whether each is active, finished, or uncertain.

The agent edits `project.json` as understanding develops. The helper validates the acceptance-relevant subset; it does not enforce a universal architecture. Extra project-specific fields are allowed. Do not store secrets in any of these files.

## Feature records

Every feature has a unique `id`, meaningful `description`, `mode` (`preserve`, `adapt`, `extend`), `status` (`planned`, `researching`, `implementing`, `blocked`, `verified`), and `acceptance` list. Each acceptance entry names a scenario ID, which must have a matching evidence record below. Keep acceptance criteria concrete in the feature description or a referenced specification.

Use `decisions` for intended differences with rationale and acceptance criteria; use `unknowns` for unresolved questions, each with `id`, `description`, and boolean `blocking`. Record scope changes explicitly, including who requested them. A milestone can cover a subset but is not the completion of the original request. `stage` is descriptive; acceptance is evaluated from evidence, not a manually assigned stage label.

## Evidence records

`validations` entries have unique `id`, `kind` (`differential`, `target`, or `synthetic`), `status` (`passed`, `failed`, or `pending`), `features` (IDs), and `artifact` (relative workspace path).

For a differential entry, its artifact must be a report produced by `sre.py compare`. The check command recomputes trace hashes and the comparison and rejects stale, failed, or synthetic evidence. Source traces require a pinned source build and actual runtime provenance. A report's contents remain agent-supplied evidence, not a trusted attestation.

For a target entry, its JSON artifact has `schema_version: 1`, `passed: true`, and nonempty `environment`, `command`, and `assertions` (list of checked acceptance statements). Record measured results and device IDs/builds as extra fields when relevant. This supports native/mobile/web tests without assuming one runner. The gate checks the declared result; it does not rerun an arbitrary command from a JSON file.

Every verified feature needs a passed target validation. Every preserved feature additionally needs passed source-runtime differential evidence. Synthetic tests help development but cannot satisfy source fidelity. Adapted/extended features require documented design decisions (a `decisions` entry with `feature`, `rationale`, and `acceptance`). A nonempty feature list and no blocking unknowns are required for recorded acceptance.

## Resume note

Record: current milestone; last successful artifact/build; failing scenario; evidence and experiment IDs; exact next command or research question; running jobs and ownership; input needed from the user. State a concrete dependency when unable to proceed. Continue other work where useful without narrowing the requested outcome.
