# Review decisions — 2026-10-12

Reviewed Fable's report against commit c409e36 and reproduced the relevant code paths. This records selected engineering changes, not an independent evaluation of autonomous reconstruction.

## Implemented

Target evidence and research observations now bind the whole artifact by SHA-256. A source capture copied outside the differential report's inputs no longer escapes drift detection. Hashes are recorded after capture, because the discovery baseline must be sealed before acceptance outcomes exist. They are not signatures or proof that a command actually ran.

Synthetic records now require valid synthetic traces. Validation IDs can differ from trace scenarios through an explicit `scenario` field. Early planning no longer requires a sealed-ready inventory. Missing build files and deeply nested JSON receive actionable errors; JSON pointer escaping/index validation is stricter. The example locates its observation by input. Regression tests cover these paths.

Added lifecycle and migration guidance, change history, contribution guidance, execution security boundaries, REA links and notices in all seven languages.

## Deliberately unchanged

- `check` remains read-only. Executing an arbitrary `command` string from evidence would change its trust boundary and still would not authenticate a historic result.
- Research contracts remain private by default: they can contain proprietary details and local paths. A user can intentionally track reviewed files in a private repository; removing protection globally is not necessary.
- The self-contained skill keeps its standard-library helpers. Packaging, type checking and broader CLI test coverage are useful follow-up work, not prerequisites for these correctness fixes.
- Shorter translations are not inherently incorrect. Different heading counts do not establish semantic drift; the translations remain and receive the same migration notice.
- Licensing and release policy require a maintainer decision. This patch does not assign a license, create a release, or claim cross-host compatibility without host testing.

## Still open

A stateful persistence example, independent agent evaluations, comprehensive machine-readable schemas, multi-host installer verification, aggregated structural diagnostics and Windows descendant-process cleanup tests remain useful work. The 417-case example tests a small stateless transformation; it cannot establish end-to-end research or reconstruction quality for arbitrary applications. None of these items is claimed complete here.
