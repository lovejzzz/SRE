# Domain validation policies

Run `sre.py domain-check policy.json --out report.json` in a policy directory. Policy/report share a directory; inputs use relative paths confined there, including symlink resolution. Inputs are normalized JSON observations produced by reviewed adapters. No PSD parser, screenshot capture, PNG decoder, or device profiler is bundled.

Every policy has `schema_version: 1`, `kind`, and nonempty `rationale`. Fix criteria before seeing results. A project validation uses `kind: "domain"`, relative `policy` and `artifact` paths, `id`, `features`, `status`. Seal pins its policy hash. `check` recomputes the report, rejects changed artifacts/policies and failures, and verifies policy binding. Domain evidence can satisfy destination validation; it cannot alone satisfy preserved source-runtime fidelity.

## Images

Policy fields: `kind: "image"`, `reference`, `candidate`, `limits: {"max_abs": 0.01, "rmse": 0.003}`. Units are normalized channel values, not percentages. Metadata must match; there is no implicit resizing or color conversion.

```json
{"schema_version":1,"width":1,"height":1,"channels":4,"color_space":"linear-sRGB","alpha_mode":"straight","samples":[0.25,0.5,0.75,1.0]}
```

Samples are row-major, interleaved, finite numbers in [0,1]. The checker reports maximum absolute error and RMSE including alpha. It validates dimensions/sample counts and fails color-space/alpha-convention mismatches. Zero thresholds permit exact comparison. Choose thresholds based on numerical accuracy and the operation, not to hide a defect. This is not perceptual equivalence, ICC conversion, Delta-E, HDR out-of-range comparison, or print-fidelity certification.

## File roundtrip

Policy: `kind: "roundtrip"`, `original`, `reopened`. Inputs have v1 schema and nonempty `document` semantic snapshots. Perform genuine save/reopen with stable identity mapping. Capture layers, masks, hidden content, metadata and editability-relevant properties. Exact document comparison detects losses hidden by a matching composite image. The adapter must do the actual roundtrip; copying JSON is not a test.

## Interaction

Policy: `kind: "interaction"`, `reference`, `candidate`. Inputs use scenario and action/result/state steps from the trace protocol. It preserves ordering, rejection outcomes and intermediate states. Include focus, selection, undo/redo and reconnect behavior when relevant. UI execution and accessibility checks remain adapter/target-test responsibilities.

## Performance

Policy: `kind: "performance"`, `measurements`, `device`, `workload`, and `limits` containing `p95_ms`, `peak_memory_mb`, `min_samples` (>=2).

```json
{"schema_version":1,"device":"specific-device-and-OS","workload":"large-document-v1","latency_ms":[12,13,14,12],"peak_memory_mb":180}
```

The checker requires matching device/workload labels, sufficient samples, and both budgets. p95 uses nearest rank `ceil(0.95*n)`. Use representative workloads and adequate samples (typically far above the schema minimum). Record warmup/profiler provenance. Declared labels are not proof of where measurements ran; an empty document or host benchmark cannot establish target performance.
