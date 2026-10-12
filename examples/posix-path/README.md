# Cross-language evidence smoke test

This example actually runs Python's standard-library `posixpath.normpath` and an independent JavaScript implementation on 417 string inputs, including 400 fixed-seed generated cases. It produces source/successor traces, a passing comparison, target evidence, and a deliberately failing mutant report, then checks recorded acceptance.

```bash
python3 examples/posix-path/run.py --workspace work/posix-run-1
```

Requires Python 3.10+ and Node.js 18+. No network or third-party packages. Output directory must not exist. Inspect `runs/mutant-comparison.json` to see the double-leading-slash defect caught by the comparator. `normalize.mjs` is the portable successor; `runner.mjs` supplies the Node input/output adapter.

Scope: lexical Unicode POSIX string paths only. Excludes bytes, Windows paths, filesystem resolution, symlinks, full Python API parity, and browser UI. The corpus is authored for this example, not an independent held-out evaluation of the skill. This tests actual cross-language execution and evidence plumbing; it does not prove autonomous reconstruction of arbitrary software or PZ fidelity.
