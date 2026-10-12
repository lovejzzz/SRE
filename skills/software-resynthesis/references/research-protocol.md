# Discovery coverage and experiments

`research.json` accompanies `project.json`. The agent collects evidence using browser/search, file, UI, language and REA tools. The helpers audit normalized records; they do not contain a crawler or automatically enumerate arbitrary menus.

## Discover and reconcile

Start with official documentation/indexes and release notes for the pinned version. Investigate a second appropriate surface: UI menus and context states, API catalogs, runtime workflows, source entry points, or file-format capabilities. Preserve URLs/paths and relevant locators. Look beyond visible buttons: options, document states, failures, persistence, external services, extensions, and cross-feature interactions.

Reconcile aliases into feature IDs without losing original labels. Every discovered item maps to a feature or a justified milestone exclusion. Unvisited surfaces stay pending; unavailable required surfaces block acceptance. A completed survey covers its declared scope, not necessarily the entire product. Two surface kinds are a minimum cross-check, not proof of completeness.

```json
{
  "schema_version": 1,
  "scope": {"claim":"milestone","description":"Selected editing workflow","source_build":"pinned-build","target":"Browser","features":["layers"]},
  "surveys": [
    {"id":"manual","kind":"docs","required":true,"status":"complete","artifact":"evidence/manual.json"},
    {"id":"menus","kind":"ui","required":true,"status":"pending","reason":"Context menus not surveyed"}
  ],
  "questions": []
}
```

A completed survey artifact has v1 schema, `source_build`, `source` (URI/path), `scope_note`, and nonempty `items`. Each item has unique `id`, `label`, and `feature`. Optional locators/raw capture paths support review. A milestone can record `disposition: "excluded"` with `reason` instead of a mapped feature; `claim: "full"` cannot exclude discovered items. Do not convert a full request into milestone completion. Valid surface kinds: `docs`, `ui`, `api`, `runtime`, `source`, `files`. Incomplete surveys need a reason.

```json
{"schema_version":1,"source_build":"pinned-build","source":"official-manual-URI","scope_note":"Layers chapter","items":[{"id":"create-layer","label":"Create layer","feature":"layers"}]}
```

Project features may have `parent` and `depends_on` IDs. References must exist and combined hierarchy/dependency cycles fail. Scope feature IDs must match the project inventory. Keep the original full request even when delivering a named milestone.

## Hypotheses and experiments

Each question has `id`, `feature`, `question`, boolean `blocking`, integer `impact` 1–5, at least two `hypotheses` (`id`, `explanation`), and `experiments`. Each experiment has `id`, nonempty object `input`, integer `cost` 1–5, and `predictions` mapping every hypothesis ID to its predicted JSON observable.

```json
{"id":"leading-slashes","feature":"normpath","question":"Keep two leading slashes?","blocking":true,"impact":4,"hypotheses":[{"id":"keep","explanation":"Exactly two are preserved"},{"id":"collapse","explanation":"All become one"}],"experiments":[{"id":"double-root","input":{"normalize":"//"},"cost":1,"predictions":{"keep":"//","collapse":"/"}}]}
```

`plan` ranks unobserved experiments by expected eliminated hypotheses under a uniform prior, weighted by impact and divided by cost. Blocking questions come first. This is a heuristic, not measured confidence. Identical predictions cannot discriminate and are omitted. Designing good hypotheses and experiments remains the agent's responsibility.

After real execution, add `observation: {"artifact":"runs/source/trace.json","pointer":"/steps/0/result/value","sha256":"<capture SHA-256>"}`. Use `sre.py fingerprint <capture>` after reviewing the capture; `audit` verifies the complete file hash, including unselected fields. Missing/stale hashes fail closed. Hashes do not authenticate the source or protect against rewriting both capture and metadata. The artifact needs v1 schema and `provenance.kind: source-runtime` with the pinned build. The JSON pointer selects the observable. One surviving hypothesis resolves the question; no survivors reports contradiction. Blocking unresolved questions prevent acceptance. Synthetic observations cannot resolve source behavior. Keep raw captures: provenance labels are declarations, not authentication.

## Seal and evolve

```bash
python3 <skill>/scripts/sre.py seal <workspace>
python3 <skill>/scripts/sre.py plan <workspace>
python3 <skill>/scripts/sre.py audit <workspace>
python3 <skill>/scripts/sre.py check <workspace>
```

Seal after discovery reconciliation and experiment design, before acceptance outcomes. It creates `research-baseline.json` without overwriting. The baseline hashes survey artifacts/domain policies and freezes scope, feature contracts, and predictions. Adding observations or changing implementation status does not invalidate it. Editing predictions to fit results, changing thresholds, shrinking scope, or altering inventories does invalidate it.

New evidence may legitimately expand the plan. Record why, preserve the old baseline, then `seal --out research-baseline-2.json` and set `project.json.research_baseline` to that file. This is reviewable versioning, not tamper-proof storage. Never rebaseline simply to hide a regression or removed requirement.

Migration from v0.1: add actual surveys/questions, pin the build and seal. Do not invent evidence to make legacy results green. `check` exposes `behavior_ready` and `research_ready`; it returns nonzero unless both pass. Full-scope acceptance still cannot prove absence of unknown, undiscovered features.

`plan` is available before the build and inventory are finalized. It validates supplied questions and ranks their experiments; a newly initialized workspace returns an empty queue until questions are added. It does not certify discovery readiness. `seal` and `audit` retain the complete inventory requirements.
