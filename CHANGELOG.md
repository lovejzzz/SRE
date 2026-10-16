# Change history

## Unreleased — review hardening

- Distinguish isolated source/successor component execution from application-runtime traces. Comparisons accept component evidence; full fidelity acceptance rejects it. Add regression coverage and apply the distinction to PZ height and inventory probes.

- Link manual UI traces to fingerprinted raw captures; reject changed/missing/escaping captures on comparison and acceptance. Existing non-UI traces remain compatible.
- Add append-only `record` and evidence-checking `report` commands, driven by the PZ browser case's need to preserve failed experiments and a complete reconstruction history. Reports do not certify acceptance; existing workspaces need no reinitialization.

- Require SHA-256 bindings for target validation artifacts and research observation captures. Older records without hashes now fail acceptance; review original captures/logs or rerun before recording fingerprints.
- Validate synthetic trace structure, provenance and scenario; synthetic evidence still cannot establish source fidelity or target readiness.
- Allow explicit validation `scenario`, defaulting to its ID.
- Allow experiment planning before source build/inventory completion; sealing and auditing remain strict.
- Reject malformed JSON pointer escapes, noncanonical array indices and JSON nesting beyond depth 128 with actionable errors.
- Explain missing adapter build files before execution, and distinguish preflight errors from retained run diagnostics.
- Select the POSIX research observation by experimental input rather than a hard-coded step index.
- Add regression tests, lifecycle guidance and synchronized migration notices in all seven READMEs.

The earlier v0.1/v0.2 labels describe development stages, not published Git tags or releases. No release is implied by this log.
