# Differential and target validation

## Adapters

An adapter owns reset, source version/environment pinning, execution, and observation. Use isolated source test data. Reset may use a debug interface; the tested action must go through the real application path. Compare observations after each relevant step, including failure and cancellation states, rather than only the final screenshot. Keep raw captures with normalized traces so a disputed result can be audited.

Normalize only representation differences such as volatile IDs using a stable, documented bijection. Preserve item identity, command ordering, failures, and timing where contractual. Do not sort away meaningful order or apply blanket numeric tolerance. This first comparator is deliberately strict JSON equality; put deliberate transformations in a reviewed adapter and record its version. Time-based/nondeterministic systems need domain-specific distributions/invariants, not fabricated deterministic traces.

## Trace format (v1)

Each trace is one JSON object with `schema_version: 1`, a nonempty `scenario`, `provenance`, and a nonempty `steps` array. `provenance` has `kind` (`source-runtime`, `successor-runtime`, `source-component`, `successor-component`, `synthetic`), `build`, and `adapter` strings. Additional provenance such as runtime, seed, OS, and raw capture paths is encouraged. Each step has `action`, `result`, and `state`, each a JSON object. `result` should include success/rejection information and contractual time if applicable. State must contain the observables relevant to the feature, not an empty placeholder.

`python3 <skill>/scripts/sre.py compare source.json successor.json --out report.json`

Exit 0 means equal valid traces, 1 means semantic mismatch, 2 means malformed input/error. Scenario names and step counts must match. Reports include input SHA-256 hashes, provenance, and the first differing JSON path. Input traces may be synthetic for comparator tests; only source-runtime versus successor-runtime can support fidelity acceptance. Files can live anywhere, but `check` requires all acceptance artifacts and referenced traces to resolve within the private workspace.

## Meaningful verification

Use provenance `source-component` / `successor-component` for isolated functions,
classes or modules invoked outside the application's normal workflow. These
traces can be compared and retained as research evidence, but cannot satisfy
application-level fidelity acceptance. Executing authentic installed code with
constructed fixtures proves only that component's observed outputs. It does not
prove the application creates those inputs, reaches that code path, or renders
the result correctly. Follow with an application-runtime experiment before
claiming the user-facing feature is preserved. Do not label a failed UI input as
a rejected application action until delivery and the expected preconditions have
been verified.

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

## Raw UI capture links

When observations are transcribed from actual UI inspection, set provenance
`observation_method: "manual-ui"` and include nonempty `raw_captures`, each with
`path`, `description`, and `sha256`. Store captures under the trace's directory;
absolute paths, path escapes (including symlinks), duplicates, missing files and
changed hashes fail comparison and acceptance rechecking. Other adapters may also
include raw captures using this format; existing non-UI traces remain compatible.

Record the inspected regions, action sequence and normalization in the adapter
notes. A screenshot only supports values visible in that frame. Do not infer
hidden item IDs, exact timing, offscreen state, or whole-system equivalence from
it. Hash checking links a transcription to stable files; it cannot authenticate
the screenshot or establish that transcription is accurate.

## Incremental actions and state units

When replacing a prototype with source-derived construction or crafting, test
repeated operations on existing state, partial damage, capacity limits, and
changes to materials or equipment between action start and completion. Verify
that rejection and cancellation preserve unconsumed resources. An isolated
successful first operation does not establish an incremental system.

Record units and meaning before reusing prototype fields: accumulated XP is not
a skill level, source action ticks are not seconds, and a health percentage is
not hit points. Preserve source rounding at the point where integer state is
created. Keep unknown conversions explicit until source execution establishes
them; do not silently fit them to an existing target timer.

For timed animated actions, verify the action clock independently from the clip
clock. Trace preparation/turning, active progress, loop rate, completion and
cancellation; source action units may include a bias absent from animation
seconds. A correctly imported clip and a passing duration formula do not prove
that equipment models, sound events, modifiers or game-level timing match.

### Lossless visual asset delivery

When changing texture encoding, compare decoded RGBA bytes including transparent RGB,
then compare the source and candidate through the actual browser's image/canvas path.
Offline losslessness alone does not prove identical alpha compositing in the runtime.
Preserve a failing comparison and retain the source encoding for affected pages rather
than relaxing visual acceptance. Report source disk bytes separately from selected
runtime delivery bytes; preserving source and compressed copies can increase disk use.

### Reference completeness before architectural fidelity work

Before treating a photo-derived layout as stable, inspect the cited project's own page
for published plans/sections and explanatory text. Record which references were checked.
A new authoritative drawing can contradict an otherwise internally consistent scene.
Preserve a recoverable checkpoint, explicitly mark superseded assumptions and prioritize
structure/circulation corrections before further decorative asset work. Keep observed
plan topology separate from inferred digital scale, hidden construction and grid rounding.
Passing placement tests or a furnished screenshot does not establish source fidelity.
