# Project contract and continuity

`sre.py init` creates a new private workspace; it refuses an existing destination. Keep this outside any public repository. It creates:

- `project.json`: schema version, original request, source/target, stage, features, acceptance obligations, decisions, unknowns, and next action.
- `research.json` and versioned baseline files: see [research-protocol.md](research-protocol.md).
- `evidence/`: raw observations and source references, kept separate from deliverables.
- `runs/`: normalized traces, comparison reports, logs, environment fingerprints.
- `implementation/`: the successor, with its own build and dependency records.
- `checkpoints/`: concise continuation notes, including owned process/job IDs and whether each is active, finished, or uncertain.

The agent edits `project.json` as understanding develops. The helper validates the acceptance-relevant subset; it does not enforce a universal architecture. Extra project-specific fields are allowed. Do not store secrets in any of these files.

## Feature records

Every feature has a unique `id`, meaningful `description`, `mode` (`preserve`, `adapt`, `extend`), `status` (`planned`, `researching`, `implementing`, `blocked`, `verified`), and `acceptance` list. Each acceptance entry names a scenario ID, which must have a matching evidence record below. Keep acceptance criteria concrete in the feature description or a referenced specification.

Use `decisions` for intended differences with rationale and acceptance criteria; use `unknowns` for unresolved questions, each with `id`, `description`, and boolean `blocking`. Record scope changes explicitly, including who requested them. A milestone can cover a subset but is not the completion of the original request. `stage` is descriptive; acceptance is evaluated from evidence, not a manually assigned stage label.

## Evidence records

`validations` entries have unique `id`, `kind` (`differential`, `target`, `domain`, or `synthetic`), `status` (`passed`, `failed`, or `pending`), `features` (IDs), and `artifact` (relative workspace path).

For a differential entry, its artifact must be a report produced by `sre.py compare`. The check command recomputes trace hashes and the comparison and rejects stale, failed, or synthetic evidence. Source traces require a pinned source build and actual runtime provenance. A report's contents remain agent-supplied evidence, not a trusted attestation.

For a target entry, its JSON artifact has `schema_version: 1`, `passed: true`, and nonempty `environment`, `command`, and `assertions` (list of checked acceptance statements). Record measured results and device IDs/builds as extra fields when relevant. This supports native/mobile/web tests without assuming one runner. The gate checks the declared result; it does not rerun an arbitrary command from a JSON file.

Every verified feature needs a passed target or domain validation. Domain records also require a relative `policy` path; see [domain-validation.md](domain-validation.md). Every preserved feature additionally needs passed source-runtime differential evidence. Synthetic tests help development but cannot satisfy source fidelity. Adapted/extended features require documented design decisions (a `decisions` entry with `feature`, `rationale`, and `acceptance`). A nonempty feature list, no blocking unknowns, and a successful sealed research audit are required for recorded acceptance.

## Resume note

Record: current milestone; last successful artifact/build; failing scenario; evidence and experiment IDs; exact next command or research question; running jobs and ownership; input needed from the user. State a concrete dependency when unable to proceed. Continue other work where useful without narrowing the requested outcome.

## Editor-built environments and persistence

When an editor is part of the deliverable, build a representative result through its actual UI. Keep its exported plan and architecture intent alongside rendered evidence. Verify meaningful routes (door clearances, stair landings in both directions, furniture access and secondary exits); a complete object list does not establish a usable environment. Test both sides of a multi-tile boundary with the actor footprint straddling neighbouring lanes.

Exercise the editor-to-runtime-to-save round trip. Stocked items must enter real containers, remain usable and survive serialization/reload. Test cancellation and invalid moves for atomic restoration, and reflooring without hiding furniture from selection. Preserve failures in the journal before correcting them.

Inspect source shaders before interpreting texture channels: alpha can encode a paint mask rather than transparency. Record the source semantics and verify the rendered result. Keep catalog coverage, architectural usability, visual fidelity and complete source-system parity as separate claims.

## Interior layers and original asset additions

Treat structural flooring, textile overlays, tabletop props and wall-mounted
objects as different placement layers. Adding a rug must retain floor support,
and furniture must remain selectable above it. Verify the complete multi-tile
prefab and each orientation in the catalog, not just the first texture. Generated
art should retain its reproducible source, provenance and runtime atlas metadata,
and ship in code-only releases when required by the new scene.

For furnishing changes, inspect each affected level at useful scale and walk the
new doorway or furniture approach. A door-open tile-route audit complements actual
actor-footprint play; it does not replace it. Do not infer believable placement
from a valid asset ID: inspect wall support, tabletop height, facing and grouped
pieces. Preserve earlier house editions before replacing a curated template.

Use one support-height rule across gameplay, editor, placement preview and saved
thumbnails. Exercise selection and moving a support together with its attached
objects. Visual checks must include fixtures beside mirrors and tall furniture;
a valid wall attachment can still overlap another object.

If an authentic walkthrough disagrees with a route replay, export the actual
save through product controls and reproduce its coordinates and object states
offline. Test near wall ends and off-center doorway approaches, including recovery
from older overlapping positions; center-to-center routes alone can miss traps.
For long-duration scenarios, separate usable finite inventory, architectural
provision and fully simulated systems. A nominal calorie total is not proof of
nutrition, water/sanitation capacity or one-year survival.


For multi-day occupancy acceptance, freeze a build and retain a source hash manifest.
Use a separate save, log performed routines and idle accelerated intervals separately,
and export day boundaries through the UI. Check needs and actual stock consumption,
not just survival or the calendar. If fixes change the living loop, run a fresh full
trial as requested; short retests and earlier days do not count toward the new run.
Verify time controls by their visible selected state **and** clock/action effects;
a successful click can still hit a pointer-transparent overlay. Sleeping must advance
ongoing needs and appliances through ordinary simulation, not add a clock offset.
Preserve failed attempts, autosave rollback and incomplete facilities in the diary.

For browser input regressions, treat background suspension as a lifecycle gate,
independent of the user's pause choice and modal state. Exercise blur + hidden +
focus ordering, held modifiers, and return while manually paused. Separate real
scroll/pinch event-path tests from physical trackpad and Safari hardware claims.
When a tiled wall has a seam, inspect source corner metadata and sprite extents
before stretching art: missing join pieces and filtered transparent borders have
different causes. Share derived joins across play, editor and previews, including
old saves and undo; version newly generated art alongside the modules using it.

For editor simplification, audit complete user tasks before removing controls.
Separate document management, construction, view state and contextual object
properties. Icon-only presentation must preserve accessible names, focus/hover
explanations and visible selected states. Exercise new → edit → save → reload →
use, including rename and undo, through the actual UI. Archive a working document
before replacement and test storage failure without clearing it. Measure narrower
layouts and distinguish workflow success from the quality of the created scene;
an audit fixture with misplaced geometry is not an approved architectural asset.

When importing large asset catalogs, audit semantic classification across the
entire inventory and compare orientations/state variants of named objects.
Source flags can conflict with the depicted purpose; preserve raw metadata and
apply narrow, evidenced runtime corrections. Sprite sheets are not categories.
For modular architecture, verify composed openings as well as individual sprite
sizes, and test traversal after repairing geometry. Keep exhaustive metadata
checks distinct from representative visual inspection and source fidelity.

For isometric editors, test visible-surface pointer coordinates separately from
floor-grid coordinates. Preview and commit must consume the same placement
intent, including support, orientation and occlusion failures. UI exports can
verify resulting coordinates without reading hidden application state. A design
roadmap records acceptance obligations; it does not mark future work delivered.

When a user reports a sparse catalog, inspect rendered card counts, viewport
height, scroll offsets, pagination and active filters through the UI. Inventory
counts alone do not establish discoverability. Reset position on navigation but
preserve it on background resource refresh; verify first and last pages.

For virtualized catalogs, verify continuous scrolling across former page boundaries,
last-item reachability, bounded mounted-node counts and selection after filtering.
Do not equate mounted DOM count with inventory size. Derive source states from
explicit transition metadata where available; unknown is not intact. When removing
DOM children during iteration, use a stable snapshot and test recycling in both
scroll directions. Preserve unmatched entries in an explicit fallback facet.

When an architectural overlay replaces a structural face, test the entire composed
assembly (doors AND windows), not only the selected sprite. Retain the supporting
opening in saved data and verify material, orientation, undo/redo, replacement,
legacy inference and unsupported-family refusal. Full-height assemblies may carry
both structure and interaction flags; do not infer layering from one flag alone.

Variant consolidation must preserve a lossless mapping to original source IDs.
Separate style, state and orientation; ambiguous entries remain individually
accessible. Validate auto-orientation with exported placements on both wall axes,
not just a rotated preview. An explicit manual rotation must not be immediately
reversed by automatic alignment. Keep verification counts labeled as cards or
source variants so a reduced catalog is not mistaken for missing inventory.
