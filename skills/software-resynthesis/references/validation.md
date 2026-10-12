# Differential and target validation

## Adapters

An adapter owns reset, source version/environment pinning, execution, and observation. Use isolated source test data. Reset may use a debug interface; the tested action must go through the real application path. Compare observations after each relevant step, including failure and cancellation states, rather than only the final screenshot. Keep raw captures with normalized traces so a disputed result can be audited.

Normalize only representation differences such as volatile IDs using a stable, documented bijection. Preserve item identity, command ordering, failures, and timing where contractual. Do not sort away meaningful order or apply blanket numeric tolerance. This first comparator is deliberately strict JSON equality; put deliberate transformations in a reviewed adapter and record its version. Time-based/nondeterministic systems need domain-specific distributions/invariants, not fabricated deterministic traces.

## Trace format (v1)

Each trace is one JSON object with `schema_version: 1`, a nonempty `scenario`, `provenance`, and a nonempty `steps` array. `provenance` has `kind` (`source-runtime`, `successor-runtime`, `synthetic`), `build`, and `adapter` strings. Additional provenance such as runtime, seed, OS, and raw capture paths is encouraged. Each step has `action`, `result`, and `state`, each a JSON object. `result` should include success/rejection information and contractual time if applicable. State must contain the observables relevant to the feature, not an empty placeholder.

`python3 <skill>/scripts/sre.py compare source.json successor.json --out report.json`

Exit 0 means equal valid traces, 1 means semantic mismatch, 2 means malformed input/error. Scenario names and step counts must match. Reports include input SHA-256 hashes, provenance, and the first differing JSON path. Input traces may be synthetic for comparator tests; only source-runtime versus successor-runtime can support fidelity acceptance. Files can live anywhere, but `check` requires all acceptance artifacts and referenced traces to resolve within the private workspace.

## Meaningful verification

- Maintain held-out cases independent of implementation-driven fixtures; cover boundary/failure/persistence behavior, not only the happy path.
- Validate adapters against visible source behavior; do not treat source-shaped mock data as an oracle.
- Deliberately mutate a behavior and ensure comparison fails. A comparator that only sees passing cases is not enough.
- Shrink a failure by replaying smaller sequences against both real runners. The included comparator reports a first difference; it does not automatically minimize an executable counterexample.
- Re-run affected checks after a fix. For preserve features, run differential and destination checks; for designed changes, use explicit target acceptance plus regressions.

`sre.py check` checks recorded obligations and detects stale differential artifacts; it cannot establish that observations are authentic, that every feature was discovered, or that manually recorded target assertions were actually executed. Keep these limits visible in the delivery report. Do not call a prototype an automatic, universal software reconstruction engine.

## Recorded evidence integrity

For differential and synthetic validations, `scenario` optionally names the trace scenario; it defaults to the validation `id`. Synthetic artifacts must be valid traces with synthetic provenance. They can supplement testing but never replace source-runtime differential or target/domain evidence.

A passed target validation needs `sha256` alongside `artifact` in `project.json`. After executing and reviewing the test, run `sre.py fingerprint <workspace>/runs/target.json` and copy the returned digest. The target file still requires v1 schema, `passed: true`, nonempty `command` and `environment`, and a nonempty string array `assertions`. `check` verifies its complete file hash without executing the recorded command.

Older records without a digest fail closed. Review the original capture and execution logs before adding its digest; rerun the test if those are unavailable. Do not silently refresh hashes after unexpected changes. A digest detects file drift relative to its record, not authenticity: anyone able to rewrite both evidence and metadata can fabricate them. Retain reviewed snapshots in access-controlled storage when stronger integrity is needed.

All JSON inputs have a maximum nesting depth of 128 (root depth zero). Split excessively nested captures or normalize them into a reviewed bounded representation.
