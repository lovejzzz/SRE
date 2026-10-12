# Contributing

Keep the installed skill self-contained and its instructions focused. Put detailed formats in references and deterministic work in standard-library helpers. Preserve the original user scope and distinguish preserve/adapt/extend behavior.

For a change, describe the concrete failure or missing capability, add a regression test when behavior changes, and run:

```sh
python -m unittest discover -s tests -v
python examples/posix-path/run.py --workspace work/unique-new-run
```

The example requires Node.js 18+ and a new output directory. Document format changes and migration in CHANGELOG.md and the affected reference. Keep capability and limitation statements consistent across the seven READMEs; identical heading counts are not required. Never commit proprietary captures, credentials or personal data. Do not label synthetic helper tests as real source execution or independent skill evaluations.
