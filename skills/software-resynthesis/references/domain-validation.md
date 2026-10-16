# Domain validation policies

Run `sre.py domain-check policy.json --out report.json` in a policy directory. Policy/report share a directory; inputs use relative paths confined there, including symlink resolution. Inputs are normalized JSON observations produced by reviewed adapters. No PSD parser, screenshot capture, PNG decoder, or device profiler is bundled.

Every policy has `schema_version: 1`, `kind`, and nonempty `rationale`. Fix criteria before seeing results. A project validation uses `kind: "domain"`, relative `policy` and `artifact` paths, `id`, `features`, `status`. Seal pins its policy hash. `check` recomputes the report, rejects changed artifacts/policies and failures, and verifies policy binding. Domain evidence can satisfy destination validation; it cannot alone satisfy preserved source-runtime fidelity.

## Images

Policy fields: `kind: "image"`, `reference`, `candidate`, `limits: {"max_abs": 0.01, "rmse": 0.003}`. Units are normalized channel values, not percentages. Metadata must match; there is no implicit resizing or color conversion.

```json
{"schema_version":1,"width":1,"height":1,"channels":4,"color_space":"linear-sRGB","alpha_mode":"straight","samples":[0.25,0.5,0.75,1.0]}
```

Samples are row-major, interleaved, finite numbers in [0,1]. The checker reports maximum absolute error and RMSE including alpha. It validates dimensions/sample counts and fails color-space/alpha-convention mismatches. Zero thresholds permit exact comparison. Choose thresholds based on numerical accuracy and the operation, not to hide a defect. This is not perceptual equivalence, ICC conversion, Delta-E, HDR out-of-range comparison, or print-fidelity certification.

Before comparing rendered output, record the coordinate contract: native versus
logical pixels, device scale, viewport, camera/zoom, asset units and anchor points.
Transparent sprite margins and offscreen render targets are not object dimensions.
Trace the complete asset-to-screen transform when apparent size or placement is
wrong, and inspect the actual result after fixing it. A plausible matrix alone
does not prove correct rendering. Match document/scene state and appearance as
well as coordinates; otherwise label the capture an alignment study. Never resize
or reposition a candidate after the fact merely to make a fidelity test pass.

Check compositing over nonempty backgrounds. Dimming color is not the same as
reducing opacity: an apparently correct sprite over black may reveal geometry
behind it when layers overlap. Include front/back occlusion and unknown-content
masking cases; keep a source layout reference distinct from a matched-state diff.

## File roundtrip

Policy: `kind: "roundtrip"`, `original`, `reopened`. Inputs have v1 schema and nonempty `document` semantic snapshots. Perform genuine save/reopen with stable identity mapping. Capture layers, masks, hidden content, metadata and editability-relevant properties. Exact document comparison detects losses hidden by a matching composite image. The adapter must do the actual roundtrip; copying JSON is not a test.

## Interaction

For transient behavior, capture a bounded trace from the actual rendering or
execution path while applying real UI input. A final resting screenshot cannot
prove that intermediate states occurred. Keep diagnostic views opt-in and avoid
changing simulation timing or replacing the normal input path to obtain a pass.

For delayed actions, change relevant world state between initiation and completion
(e.g. close or obstruct a passage during traversal). Check cancellation and
completion against current state, not only initial eligibility. Preserve the
counterexample and distinguish fixture tests from real application input.
Determine which phases permit interruption in the source: rechecking every
condition at every stage can itself change behavior after an action commits.
Do not assume animation end, gameplay completion and control release coincide;
trace the events that cause each transition.

Policy: `kind: "interaction"`, `reference`, `candidate`. Inputs use scenario and action/result/state steps from the trace protocol. It preserves ordering, rejection outcomes and intermediate states. Include focus, selection, undo/redo and reconnect behavior when relevant. UI execution and accessibility checks remain adapter/target-test responsibilities.

For queued interactions, distinguish destination selection, route discovery,
movement, arrival revalidation, and the final action. A correct selected square
does not prove a reachable route. Check cancellation and obstacles introduced
mid-route; preserve partial movement rather than teleporting to the destination.
Record the target object identity when several controls share a label, and retain
failed routes alongside successful ones. Navigation budget exhaustion is not
proof of unreachability. Component selection fixtures do not validate the source
game's navigation or action handoff.

## Time-dependent media

For time-dependent media, distinguish intrinsic asset duration from effective
playback timing. Trace the consumer's rate, randomization, state transitions,
blend weights and event timing; a serialized field may be unused in the active
path. Execute the source component where possible, but also observe the running
application under matched state and input. A frozen frame proves neither motion
timing nor transition fidelity. Preserve unresolved references and loader warnings
instead of silently treating discovery or partial parsing as runtime coverage.

Validate transitions as well as stable states: outgoing and incoming phases,
weights at intermediate times, interruption/reversal, pause and completion.
Some edges use dedicated transition assets rather than a generic blend. Keep
those obligations explicit. Render caches must include every active pose and
weight; correct state values alone do not prove that the displayed pose uses them.
For traversal, capture animation phase, world coordinates and collision/control
state together. A correctly selected clip can coexist with missing root motion,
a wrong landing position or controls that remain locked after completion.

For one-shot media, verify the exact final sample and behavior beyond its end;
looping playback can hide a missing terminal pose. Resolve absent transition
settings through the source's actual fallback and inheritance rules. Keep an
isolated asset preview distinct from automatic activation in the product flow.

## Performance

Policy: `kind: "performance"`, `measurements`, `device`, `workload`, and `limits` containing `p95_ms`, `peak_memory_mb`, `min_samples` (>=2).

```json
{"schema_version":1,"device":"specific-device-and-OS","workload":"large-document-v1","latency_ms":[12,13,14,12],"peak_memory_mb":180}
```

The checker requires matching device/workload labels, sufficient samples, and both budgets. p95 uses nearest rank `ceil(0.95*n)`. Use representative workloads and adequate samples (typically far above the schema minimum). Record warmup/profiler provenance. Declared labels are not proof of where measurements ran; an empty document or host benchmark cannot establish target performance.
For UI stalls, profile the actual user action with the surrounding UI active: background
render loops can dominate a storage task even when its codec yields. Preserve raw samples
and terminal receipts. A profile's capture duration includes idle and tool delays; never
report it as operation latency or compare different capture lengths as a speedup. If
background work is suspended under a modal, verify that closing it restores rendering
and that persisted content is unchanged. Re-measure latency separately against its budget.

## Equipped model validation

Trace the full attachment chain: parent bone, parent attachment, item attachment,
mesh transform and model scale. Verify actual default flags before assuming a
self attachment is inverted. Compare isolated matrices separately from rendered
game poses. Vertex point-set agreement alone cannot validate UVs, topology or
animation placement. Include equipment in render cache identity and test changes
while animation time is frozen, plus same-instance two-hand deduplication.

## Interaction eligibility and partial failures

Inspect disabled actions and their explanatory tooltips before attributing a
failed input to distance, focus or missing support. Keep menu eligibility checks
read-only; trace the execution path separately, including state changes made
before a later failure (for example, unlocking before obstruction prevents an
opening). Test both the refusal and its surviving state changes. For nested
inventory lookups, match the source's permitted container kinds: a specialized
key-ring search is not equivalent to recursively searching every carried bag.

## Source experiment initialization

When a rare prerequisite makes a source experiment impractical, a documented
initializer may prepare isolated test data. Keep preparation separate from the
behavior under test: identify the exact mutations, guard the intended save or
project, and avoid replacing action implementations, clocks or result functions.
Back up unloaded source data first and retain a digest manifest. Make repeated
initialization idempotent, including partial failures, and verify the resulting
state through the real application before collecting action evidence.

Record initialization code, activation scope and runtime confirmation alongside
the experiment. A created plugin file is not proof that the application discovered
or executed it; inspect loader rules and caches when activation fails. Confirm a
process has exited before restarting it. Label prepared-state source runs clearly:
they can establish behavior from that state, but do not prove that normal gameplay
can acquire the prerequisites. Preserve a separate natural-acquisition obligation.

## Active dispatch versus retained implementations

A matching class or action name in an installed build does not establish that the
current user workflow invokes it. Trace from the actual UI handler through its
selected recipe, factory and callbacks before adopting costs, timing or effects.
Applications may retain legacy implementations alongside newer entity systems.
When runtime results contradict a static candidate, preserve the contradiction,
identify the active route, and revisit every contract derived from the old route
(including time, rewards, tools, effects and visual state), not just the first
visible mismatch. Keep component evidence valid only for the component actually
executed; do not promote it into workflow evidence.

When an active route crosses frontend scripts and backend/native actions, resolve
which layer controls the requested execution mode. A multiplayer server timer
may differ from a single-player queue override. Record override precedence before
converting units. For rewards, distinguish a recipe's base award from the final
player gain: trace default reductions, initial-character boosts, traits, books,
world options and numeric precision. Test the default character as well as
explicit modifiers; absence of a boost is not necessarily a multiplier of one.

Separate temporary presentation overrides from underlying application state.
An action prop need not be an equipped inventory item. Trace explicit-empty versus
missing override semantics, both-hand replacement, and when an override starts
and ends. Check cancellation, completion and save boundaries for restoration of
previous state; include nonvisual side effects such as weight, selection and
ownership so a visually plausible fix does not silently change gameplay.

### Recipe inputs: identity, eligibility and retained tools

Trace input selection beyond displayed item names and counts. Check tags, per-instance condition/broken state, favorite restrictions and keep/consume flags independently. Verify rejected inputs cause no partial consumption or rewards; mutate selected inputs during a queued action and check revalidation. Preserve exact retained and consumed identities in exported evidence. Distinguish direct inventory coverage from nested bags, nearby containers and ground material search. A fixture exercising a source-derived rule is target evidence, not a source-runtime differential.

When broadening accepted gameplay inputs (tags, variants or equipment families), enumerate their transitive presentation dependencies too: model, material, texture, attachment and sound. Cross-check accepted catalog variants against imported resources; test at least a materially different variant in the actual target renderer. Successful data selection alone does not prove a usable or visually faithful path. Record missing UI entry points separately from state-field support.

For user-marked item state, inspect who owns the mark and who interprets it (global item flag, character name, account or session). Do not collapse distinct marks into a shared boolean. Exercise move destinations inside and outside the ownership tree. Validate fixture values against the selected item definition after changing a type: bounds, capacity and dependent variant fields must remain possible in the source. Preserve impossible fixtures and label prior results as limited; rerun with a valid fixture rather than silently replacing historical evidence.

For placement and queued workflows, measure eligibility at each stage separately:
menu entry, preview, approach, action start, and final commit. A green cursor or a
progress bar does not prove input acceptance or a world mutation. Correlate the
visible action with a terminal log/state change and inventory deltas. Establish a
positive control at the same reachable world target; camera movement invalidates
reused screen coordinates. Change one eligibility mark at a time, verify its UI
state, and preserve failed attempts. If the source performs an action before
rejecting at commit, immediate target rejection remains a workflow mismatch even
when both protect the same materials. Do not encode the earlier assumption as a
permanent test expectation; revise it from the stronger runtime evidence.

Do not assume failed operations are globally transactional. Trace side effects
before and after the failure point separately: wear, sounds, equipment replacement,
world metadata and rewards may have different commit boundaries. For randomized
wear, preserve the actor/item identity at each call site, call order, conditional
RNG draws and secondary condition channels. A successful recipe can damage a
retained input; a failed recipe can still damage an equipped item. One unchanged
sample cannot establish absence of wear. Verify forced boundary outcomes in
component tests and ordinary source-runtime behavior separately.

When extending asset ingestion to a new format, inspect actual source extensions
and loader flags instead of assuming a shared representation. Preserve node
hierarchy/transforms and reject unsupported skinning explicitly. Check finite
geometry, index bounds and UV cardinality, but keep these structural checks
separate from source-loader transform equivalence and rendered visual fidelity.
If the installed native loader can run in isolation, compare its output before
adjusting assets by eye. Track handedness, hierarchy matrices, UV origin and
triangle winding at each pipeline stage; a later conversion may undo an earlier
one. Keep a failing comparison against the old importer as a regression control.
Label native-loader probes as component evidence, not in-game rendering evidence.

For asset selection, resolve the concrete runtime type's overridden getter before
mapping script properties to assets. Probe precedence and distinguish absent,
null, empty and invalid indexed values; a truthiness fallback can silently select
the wrong model. If a probe bypasses construction and initializes fields directly,
label it as getter-only evidence. Creation-time variant selection, persistence and
rendering still require separate verification.

When wiring a previously isolated callback into gameplay, follow its outputs
through inventory identity, equipment replacement, world placement, rendering,
pickup and save/load. Check that newly reachable asset names exist in the runtime
bundle: a successful item mutation can still equip an invisible object. Preserve
the source's failure ordering; a later recipe rejection must not erase earlier
tool damage. Keep deterministic boundary tests and ordinary runtime trials
separate, and record whether a trial began from a synthetic state.

Do not infer state ownership from a method parameter name. A getter taking a
tool may still consult the actor's equipped item or shared state. Exercise cases
where the supplied item and equipped item differ, including unarmed actors and
skill boundaries. Preserve observed source arithmetic rather than replacing
surprising initial values or rounding with a more intuitive formula.

For compound actions, test threshold crossings within the action, not only steady
states before and after it. An early XP, capacity, permission or ownership update
may change the parameters of a later callback in that same action. Trace the
source call order and check the resulting downstream behavior at the boundary;
separately label static ordering evidence and actual source workflow execution.

When progress exists on both an object and its owner, identify which value wins
when an action starts and which values updates persist. Check a second copy of
the same object type and a different owner; object-local progress alone may not
represent the application's actual resume semantics.

Separate serialized representation, setter behavior, and action eligibility.
Do not add a clamp merely because a value is unusual: probe the source setter
and the consuming action separately. Reject malformed target encodings without
silently rewriting source-representable state into a different valid state.

During source UI exploration, inspect the object's action menu and disabled-action
reason before repeating a failed approach or movement. Transparency and occlusion
can make a closed or locked barrier look open. Record prerequisite state changes
made to reach the scenario. Identify the concrete sample variant: observing an
entertainment book does not validate skill-book XP, and accelerated playback does
not establish normal-speed timing or audio-event fidelity.

When an action selects a dynamic visual asset, validate the selected asset in the
rendered action state. A valid animation clip and hand-override identifier do not
prove that its prop model or texture was imported and drawn. Preserve a missing
prop capture, fix the asset dependency, and capture the action again; do not use
an idle screenshot or a generic prop as evidence for the selected item variant.

Trace user-visible names back to persistent identity before constructing repeat,
cache, or save fixtures. Localized labels, padded numbers, translation keys and
internal IDs may differ even when they identify the same visible item. A fixture
that supplies a display label as an ID only validates behavior for that supplied
key; it does not validate source identity generation. Preserve that distinction
when later evidence corrects the fixture, and test identity separately from
presentation and localization.

For audio captures, separate asset decoding, isolated event rendering and actual
application playback. Record sample rate, channels, native event/runtime version,
parameters, listener context and timing origin. Nonzero samples only prove that
a capture contains signal, not the correct event variant, mix, onset or fidelity.
Offline output can include initialization/loading frames before event start;
record the native mixer clock at start and preserve raw audio before any trimming.
Do not infer an event's intended delay from the first nonzero sample alone.

When recording browser audio, capture the actual mixed stream rather than only
logging play calls. Keep the original container, event clock and recorder start/
stop clocks. Distinguish decoded frame duration from container timestamps: codecs
or capture pipelines can leave packet-time gaps, and concatenating decoded frames
can shorten the timeline. Preserve an explicit timestamp-aware decode for timing
analysis. A nonzero mixed capture and event trace still do not prove physical
speaker output or perceptual equivalence to the source application.

When expanding a working subtype to a source registry, inspect the complete
registry for identity aliases and exceptional parameter families before sharing
its implementation. Verify independent state keys and exception cases, then
check the actual UI dispatch and each required dynamic asset dependency. A
registry-wide static comparison proves configuration coverage only; it does not
prove each subtype's application workflow or downstream effects.

For games that sample input once per frame, preserve the key hold duration with
the observation. A zero-duration key press can be missed even with correct focus;
verify an adequately held press before classifying a command as unsupported.
When checking transient counters, an exact-value wait can miss an already-passed
state. Preserve the timeout, observe the current action, and do not restart it or
claim same-time differential parity from unmatched interruption points.

A learned/unlocked identifier, a completed-content record and an enabled action
are separate obligations. Compare their exact keys and persistence independently.
A component probe with an empty registry can establish identity/deduplication
semantics, but cannot prove expansion, prerequisites or downstream availability;
record that registry state and verify the consuming feature with real definitions.

When an API has several overloads or a visibility override, trace the exact
overload used by the consumer. A display/discovery permission must not silently
become execution permission. Probe both answers under the same configuration
and read back injected settings. For declarative registries, inventory embedded
components as well as standalone definitions; retain conflicting declarations
until native load order and inheritance are known. A file scan is not a loaded
runtime registry or evidence that its actions work.

Record the native initialization phase when comparing imported declarations.
Parsing, reference resolution, post-load callbacks and UI overrides may produce
different values. Compare consumer getters as well as stored fields: missing
declarations can receive fallback values at read time. Preserve ordered repeated
properties when the source appends rather than replaces them. Missing registry
dependencies in a probe are probe limitations, not source application defects.

For quantity-based workflows, distinguish a selector's common amount, per-variant
amount, unit, mode and final mutation. Matching parsed quantities does not prove
correct consumption or retention. Count child resources separately from top-level
inputs; a list of item inputs can still contain nested fluid/energy operations.
Keep variant-specific quantities when the source normalizes a common getter.
Before introducing persistent state for a getter, inspect whether it delegates
to a definition or subclass. A depletion policy can be derived from script data
rather than an independent instance flag; probe construction must preserve that
delegation instead of inventing a field or bypassing the getter.
Do not assume factory initialization and a later setter use the same numeric
conversion. Compare rounding, saturation and intermediate precision at both
entry points, including whether a setter can produce values beyond a reported
capacity. Test exact float bits when decimal serialization hides differences.

For depletion or replacement workflows, assert both outputs and retained inputs.
Check replacement creation separately from removal: a destroy flag may affect
only the latter, and a retained empty input may still produce an output. Verify
which fields cross the replacement boundary, including selective metadata and
rescaling between different capacities. Do not infer complete factory or UI
coverage from a successful isolated state-transfer call. When using constructor-
bypassing probes, carry forward discovered initialization dependencies (definition
objects, random services, registries); a repeated missing prerequisite is an
adapter defect, not a new source behavior.

When a setter updates multiple related fields, capture every affected field and
the no-op/early-return paths. Similar getter names need not return the same value:
a later branch may overwrite actual weight while retaining an earlier display
weight. Match binary precision and mutation order before integrating downstream
capacity checks; a correct interpolation formula alone does not prove the state
transition. Exercise real registry lookups when a branch depends on another
definition, including an absent entry, without replacing the lookup method.

For derived consumable quantities, re-read the source getter after mutation;
integer subtraction may not equal a float-backed getter after rounding. Inspect
getter modifiers before treating returned values as raw fields: age, cooking or
other state can modify a value before a setter scales and stores it. Include
zero-denominator and signed-zero cases, and distinguish source nonfinite results
from the target save format's ability to retain them. Keep failed comparisons
when they expose these semantic differences.

Separate parsed declarations from resolved runtime references. A public getter
may expose loaded names while another getter queries a resolved list that is
still empty. Before comparing execution, run the source's required registry and
post-load phases, then inspect a dependent lookup. Do not change target behavior
to match a probe's missing initialization. Preserve pre-resolution observations
as lifecycle evidence, and state when collection order is supplied by the probe
rather than reproduced by the target's own selection algorithm.

Persist full UI snapshots at assertion/checkpoint boundaries when the inspection
tool normally emits deltas. Missing unchanged text in a delta is not evidence
that the application removed it; retain the delta and obtain a full snapshot
before diagnosing a UI regression.

For transient completion messages, verify the durable postcondition as well as
the visible workflow. A missed toast is not proof of failure or success. Inspect
the action state and exported result before repeating a mutation; preserve the
observation failure and restore isolated test fixtures after verification.

When porting flag-driven eligibility, test absent flags, each flag, contradictory
pairs, and subtype/ownership bypasses. A flag's name does not define its scope:
non-applicable subclasses may pass, and earlier branches may take precedence.
Keep getter-state predicate probes distinct from validation of the code that
derives those states and from full candidate selection.

When resolution removes missing names or duplicates, verify parallel positional
arrays rather than assuming they compact together. Keep membership caches and
quantity-lookup indexes distinct; test aliases, case variants, and wildcard
branches. State whether registry/tag iteration order is observed or supplied.

For accelerated simulation workflows, capture the in-game clock and durable
progress rather than assuming a wall-clock timeout equals simulated completion.
Background rendering and UI updates may throttle progression. Do not restart a
live action merely because a notification wait expired; inspect its state.

For world placement workflows, exercise both a visible reachable destination and
an adjacent destination separated by a wall. Do not infer reachability from an
interaction helper that intentionally stops short of a solid object. Verify the
placed object in the rendered world, its collision/interaction, and its persisted
contents; a new save record alone does not prove usable placement.

For hosted builds that depend on user-local assets, validate a cold import and a
warm reload on the actual deployed origin. A localhost run with files on disk
does not exercise the browser cache, origin-separated saves or static hosting.
Record which files were published and which remained local, and distinguish
successful deployment from whole-product acceptance.

### Locale and deployment changes

When the user changes the product language, verify loaded catalogs and existing saved labels as well as UI literals. Exercise cached-asset and fresh-asset paths; preserve item identities and behavior while changing presentation. A warm developer browser does not prove a first-time visitor can launch. Record subsequent explicit asset/deployment authorization separately from earlier deployment assumptions, without treating an authorization statement as proof of a third-party license.

For a custom-domain launch, verify the final HTTPS origin rather than stopping at DNS resolution or a successful build. Check certificate validity, HTTP/www redirects, a first visit without a developer asset cache, the primary interaction and save/reload. Keep authentication and TLS verification enabled. For lossless asset optimization, preserve source files and prove the decoded data is unchanged before comparing the rendered result.

When deployment testing reveals stale client files, give related scripts and styles a content-derived release version and verify an existing browser receives the corrected rendering. Successful hosting builds alone do not establish that a returning visitor loaded that release.

### Intentional presentation improvements

When a user requests smoother visibility or proximity prompts, record the change as an adaptation with its own acceptance criteria. Keep presentation fades separate from authoritative line of sight, collision and interaction reachability. Verify intermediate transitions and target changes during movement, not only settled screenshots. The displayed keyboard hint and the dispatched action must resolve the same current reachable object; test neighboring objects, removed targets and modal input suppression.

For dense interaction HUDs, validate the collapsed state, disclosure exclusivity, keyboard dismissal and one real action from each new access path. Periodic UI refresh must not replace focused controls when their content is unchanged.

### Creative editors and imported catalogs

An imported definition count is not a usable-object count. Track definition,
preview, assembled geometry/layers, placement footprint, runtime behavior and
save/reload separately. Multipart objects, layered vegetation and vehicle
materials need rendered inspection; a successful mesh conversion does not
establish a complete appearance. Retain unresolved entries in coverage records.

Verify editor-to-runtime transitions: replacing the map must update collision,
level enumeration, rendering and persistence together. Exercise a lower-floor
staircase in both directions and a second upward connection with real movement.
Test placement cancellation, undo/redo and interrupted pointer capture as
transactions; a canceled move must restore its original object. Preserve the
live save before applying a draft, and keep synthetic layout fixtures distinct
from user-created layouts and native-source comparisons.

For menu-to-world camera transitions, test coordinate continuity when the preview
viewport expands, then inspect actual intermediate frames and the final playable
state. A HUD element with zero opacity or an inert ancestor may still satisfy a
browser visibility wait; wait for the blocking transition layer to finish and
verify focus/input restoration. Keep presentation motion separate from elapsed
simulation and player input during the transition.

For photo/reference roundtrips, identify raster format from bytes rather than a
filename extension or a browser-provided MIME label. Screenshot providers may
return JPEG bytes even when the capture was saved with a `.png` name. For lossless imports, preserve
original bytes, dimensions, source credit and observation/inference notes across
actual import, refresh, export and reimport; compare decoded export bytes against
the input. When size limits require a working copy, preserve the source file,
record its dimensions/byte count/content hash, label the derived image, and verify
working-copy bytes across the roundtrip separately from source provenance. Test
a representative full-size external input early: a small fixture can conceal an
upload limit that prevents the intended workflow. A renderer screenshot used as an import fixture proves storage and UI
behavior only, not reconstruction fidelity against a real reference photograph.

For large-reference storage adaptations, measure a real history-bearing snapshot,
not just one image or a synthetic highly compressible string. Repeated long image
payloads may require interning before compression. Verify the actual storage
write, reopen, undo and normal export, and compare complete semantic content with
the pre-change export. Report persisted size separately from in-memory history
cost and other storage backends' quotas; one reduction does not prove all three.

For editor locks, verify dependent edits as well as direct gestures: moving a host
must not move a locked attachment, and shared wall changes must respect a locked
room. Exercise public automation and normal UI with the same invariant. Distinguish
explicit unlock/history restoration from accidental bypasses, and restore the
pre-test user document with a semantic export comparison.

For visual editors, verify immediate rendering after consecutive edits in the same
session, then reopen separately. Correct exported geometry and a successful reload
do not prove the live render loop survived. Preserve timestamped console failures
and compare post-fix events; placement effects can fail when a queued animation
frame predates a newly created effect. Test negative elapsed time and inspect the
actual subsequent edit, rather than using reload as a workaround or success proof.

When a browser contradicts freshly tested source, distinguish a stale loaded
module from a failed patch. A server-side source read alone does not establish
the running browser build. Verify a version-specific visible behavior and, on
the isolated test page, reload without cache if needed before repeating the
acceptance action. Do not reset user storage to solve code-cache discrepancies.

For mounted editor objects, verify the complete support graph, including fixtures
spanning several hosts. Partial host movement must either preserve the assembly
or reject atomically. Scoped inspection must include every support dependency,
and locks on dependents must constrain edits to their hosts. Separate explicitly
modelled attachments from legacy visual overlap; do not claim both are covered.

When an editor reattaches an object to a different support, verify persistent
object identity as well as the rendered result: orientation may change while the
object ID must survive and support references must change. Test detach/attach as
one atomic command, with cancellation, invalid targets, locks, undo and reopening.
If asset-family metadata is generated, check generator/output parity; a manually
patched generated catalog is not a durable fix for duplicated orientations.

When extending a rectangular editor to irregular geometry, audit every consumer
of the old bounding box: filling, hit testing, overlap, locks, cutouts, copying,
roofs, measurements and deletion. Use a concave fixture with an empty notch and
a second room in that notch. Verify the rendered boundary and inspector update
after split/merge, in addition to exported cell counts. Normalize rectangular
results so existing rectangular tools retain their capabilities.

For grid editor dragging, distinguish the continuous grab point from the occupied
cell. Flooring the cursor position can create a dead zone when a wall lies exactly
on a grid boundary. Verify a single-cell drag from the visible handle, not only a
large displacement, and check that the inspector updates immediately. Preserve
host identities in the export as separate evidence from the visual deformation.

For live game input, an action's return is not proof that the displayed position
has updated. When a movement outcome is ambiguous, capture a subsequent rendered
observation and verify position on the destination side before declaring a
collision defect or success. Exercise both directions through moved openings.

For version recovery, a listed checkpoint is not evidence that work is recoverable.
Change a visible feature, restore the named version, then actually restore the
pre-replacement checkpoint and verify the earlier feature returns. Test both
checkpoint-write and draft-write failures: neither may change the live document
or history. Verify branches get independent scene identity while retaining entity
references, and distinguish content equality from expected revision changes.

When a recovery workflow writes immutable archives and a mutable draft in separate
stores, test failure between the writes and retry after reopening. Preserve a safe
archive left by partial success and reuse it by request identity/content; do not
claim cross-store atomicity. Exercise the same request after undo and refresh:
its historical receipt must not reapply the edit. Show the current revision beside
the receipt revision so successful retry output cannot imply current scene state.

For photo-to-scene correspondence, validate the binding vocabulary against the
actual required anchors, including hosted openings rather than only rooms and
furniture. Move the host, delete the target, edit the unresolved annotation, undo,
and reload. A missing target must stay explicit; editing notes must not silently
clear its identity. Use the same entity resolver in validation, navigation and
queries, and omit raster payloads from scoped evidence queries.

For spatial editors, exercise geometry at actual map coordinates and at supported
positive/negative coordinate limits, not only near the origin. Compare translated
outputs, occupied area, boundary closure and physical edge lengths. Perform
fractional clipping in local coordinates to avoid cancellation in world-space
area calculations. Treat geometry predicates as component evidence: rendering,
picking, actor clearance/contact retreat, visibility and persistence must consume
the same shape and pass their own integration checks before exposing a new tool.

Exercise editor-to-runtime handoff with the accumulated real reference payload,
not only empty fixtures. Photos and backups can exceed synchronous storage quota
even when the editor itself persists correctly. If handoff replaces live state,
verify backup and replacement commit together, legacy recovery remains readable,
and a failure after the backup write leaves both stored records and live state
unchanged. Reload the game after a successful real handoff, not just the editor.


For continuous spatial operations (offsets, dilation, clipping), verify occupied
points against an independent geometric predicate as well as area and snapshots.
Discrete translated copies may leave holes even when their bounding box looks
correct. Declare the supported geometry vocabulary and distance convention;
never use the same transformation code to manufacture its expected test result.


When an adapter moves visible objects from a legacy tile list into derived
geometry, update resource preflight to enumerate the derived components too
(frames, leaves, surfaces and overlays). A clean legacy asset scan is not full
coverage. Inject a missing derived component and verify handoff refuses before
changing the live scene or persisted replacement.


When a geometry extension changes the coordinate model, audit interaction consumers
as well as drawing and collision: approach points, facing, animation translation,
landing footprints and side-dependent state may still assume the old grid. A
visible opening and a ray test do not prove usable traversal. Exercise both sides,
all supported orientations, blocked landing and save recovery through the actual
interaction flow. Derived-asset preflight must include reachable visual states
(open, broken, removed), not only the default appearance.


For restore/import acceptance, begin from meaningfully different content: importing
an identical snapshot can legitimately be a no-op and proves no reconstruction.
Compare exported semantic content, check history effects rather than assuming every
success creates an undo step, and restore the exact baseline after test cleanup.
Composite identity must also be remapped when copying levels or documents; otherwise
an apparently local removal can affect a different floor.


### Sparse prefabs and partial-cell collision

For a rotated multi-part asset, validate the occupied-cell set instead of assuming
its bounding-box origin is occupied. Test every supported orientation, attachment
closure, and four-turn identity. When replacing full-cell collision with polygon
geometry, audit all consumers of the old solid flag (movement, spawn, traversal
landing and NPC placement). Check actor-body clearance, not only a free center
point. Reject unsupported/invalid collision metadata conservatively. Geometry
tests do not establish rendered seam quality; inspect the assembled asset in the
actual editor and gameplay. Record decorative equipment separately from functional
interactions.

### Parametric openings versus source-image dimensions

A larger window sprite does not prove a larger usable opening. Validate the host
wall, aperture, retained sill/lintel/jambs, leaf artwork and runtime traversal as
one contract. Use physical wall-plane coordinates rather than atlas dimensions;
check asymmetric openings use their actual centre for approach and crossing.
Audit consumers that previously found openings only in tile arrays: picking,
attachment validation, erasure, depth order, save/import and material replacement.
Test both structural orientations, and preserve unsupported legacy content rather
than silently replacing it with an incompatible cutout. Record character death
or environmental interference honestly; recover through ordinary save/new-game
controls, not hidden health edits, and do not count a short traversal as a residence
simulation.

### Generated material catalogs and visual repetition

Keep internal generated surrounds/state fragments available to compilation without
presenting them as duplicate user-placeable objects. Verify a material's orientation
family separately from its automatic opening geometry. Inspect repeated surfaces in
an actual room: an isolated texture can look plausible while repeated patches read
as camouflage or seams. Reject and revise that visual failure even when topology and
asset tests pass. Repainting must retain opening IDs, attachment bindings and photo
correspondences; distinguish per-wall material assignment from actual independent
inside/outside finishes.

### Opposite faces and inspection modes

For walls or other two-sided surfaces, validate each side independently, including
shared ownership by adjacent rooms and direction changes during reshaping. Compare
both rendered views against the same saved entity IDs. Inspection views must be
explicit and must not mutate exported authoring data or silently become runtime
state. A successful inspection screenshot does not establish new camera behavior,
walkthrough correctness, or automatic material inheritance for new partitions.

### Supported storage and mixed authoring batches

When a container attaches to a moving wall, test its contents as well as its sprite:
stock must follow the host's position/orientation and become loose inventory when
the fixture is removed. Display stock from actual inventory, using declared shelf
slots; do not bake apparently usable supplies into decorative artwork. Exercise
mixed command orders such as item placement followed by wall editing. A deferred
legacy buffer can otherwise disappear when the semantic scene is recompiled. Keep
legacy furnishing regression tests when fixing that boundary, and record any failed
iteration rather than accepting the first new-feature-only green run.

### Isolated playable inspection and saved-state integrity

When a user-facing editor offers a temporary walkthrough, isolate both simulation
state and mutable world state. Label any disabled hazards, retain normal interaction
and collision rules, and keep the original saved-game application path available.
Test returning, repeated entry, and reloading mid-preview; compare original save
exports, including injuries, inventory, clock and world changes. Autosave and unload
handlers must not persist temporary state. Report inspection conditions explicitly:
a healthy preview character with hazards disabled is useful building evidence, but
cannot establish survival balance, residence duration, or autonomous AI behavior.

### Boundary-mounted visuals in playable views

An editor screenshot does not validate runtime visibility of wall/window attachments.
Walk on both sides of the support, approach and retreat, and inspect each component of
multipart coverings. Boundary-mounted art must inherit support visibility and cutaway;
sampling only the exterior cell can hide half a covering while its window remains visible.
Verify that the correction changes presentation only: unrelated rooms and other floors
must not become explored or visible. For multi-part interactive openings, operate each
part through the normal controls and retain distinct state keys in the recorded output.

When repairing mixed semantic/legacy authoring, measure representative batched edits too.
A correct per-cell full reconciliation can make a drag unusable. Batch only compatible
operations, retain atomic failure and ownership checks, and explicitly exclude structural
assets that happen to carry floor flags (such as stairs). Report observed latency separately
from percentile/frame-rate acceptance.

For stateful editors, exercise command saves with a full undo history, not only fresh
fixtures. Distinguish restoring untrusted on-disk history from staging edits against
already-validated immutable history. Measure commit work and preserve failed-write
isolation, idempotency receipts and undo depth when removing redundant compilation.
A recovered draft proves durability only; a renderer crash still needs separate stability
investigation and must not be called fixed from a single successful save.

Asset pipelines must isolate source regeneration as well as final encoding: staging only
compressed outputs cannot protect a live source atlas overwritten by an earlier generator.
Inject a failure after successful generation and assert every published byte is unchanged.
Distinguish rollback for recoverable I/O errors from crash-atomic multi-file publication.

For browser asset equivalence, bind rendered evidence to the intended build. Verify the
actual fetched source and delivery hashes against the local build manifest before decoding;
two identical stale images are not evidence for current output. Exercise a stale-server
negative control. Validate semantic state links and output ownership before generators
publish, rather than trusting pixel equality to establish catalogue integrity.

Continuous multi-leaf openings need a seam-crossing collision test with both leaves open,
as well as independent closed/open passage tests. A zero-length residual jamb can still
block a finite-radius actor even when the rendered aperture looks clear. Validate grouped
editing separately from per-leaf runtime state, and retain existing IDs when widening an
opening so saved state/provenance bindings remain meaningful.

## Reusable visual-asset learning

When a reconstruction exposes a missing asset family, retain the reusable source recipe,
support/collision/direction contract and one rendered integration example, then link that
example from the project's authoring guidance. Record which parameters actually work in
code; a recipe manifest with empty parameters is not a parametric authoring tool. Promote
lessons such as host-following transforms and material world scale into shared behavior or
regressions, while keeping the scene's coordinates and uncertain interpretation in its case
record. Validate artistic similarity separately from format compression and functional tests.

For editors with a retained legacy layer and compiled structural document, test
heterogeneous command sequences, not only each operation in isolation. In particular,
delete a legacy overlay then perform a structural edit in the same transaction;
assert the removed content stays absent in preview, commit, undo/redo and reload.
Synchronize authoritative representations before the next operation recompiles,
and propagate synchronization failure rather than silently reporting success.

For grid editors, distinguish a boundary's geometry from its storage cell. A north/west
edge may be stored in a void cell while resting on the neighboring slab. Permit only
authoritative boundary geometry with independently validated support; do not exempt all
objects sharing a wall flag. Test void preservation, rejected interior placement, collision,
undo/reopen and the public edit path. A temporary full wall proves placement support but
does not prove that the intended railing art or visual fidelity is finished.

For large-coordinate 3D scenes, compare source numeric precision with GPU attribute
precision before blaming textures for lost small detail. Subtract a local origin before
Float32 conversion, retain authoritative world coordinates on transforms, and verify
batching, picking, bounds and mounted-object edits still agree. A precision test proves
coordinate preservation; only matched rendered comparisons can attribute visible artifacts
to that cause. Record fixed-width shadow filtering separately from physical area-light or
contact-hardening transport, and measure frame cadence after increasing sample counts.

When auditing an indirect-light capture, verify its environment boundary conditions:
black background omits visible sky even if the final scene has ambient fill. Keep
irradiance versus radiance units explicit, include geometry occlusion during capture,
and remove duplicated unconditional interior fill when publishing transported light.
Validate sealed openings and shadow visibility separately from SH integration math.
For exposure complaints, distinguish hard channel clipping from perceptually washed-out
materials; compare fixed-view images and retain readable shadow paths, not just a lower
maximum pixel value. A palette revision should preserve material/source provenance.

- For volumetric hard-surface migration, inspect existing geometry before adding another smoothing layer. Recipe-authored manufacturing chamfers should preserve dimensions and object identity and regenerate collision from the same canonical geometry. Skip soft/curved/detail meshes unless explicitly supported. Validate removed corner volume and face winding, not just vertex count. Judge whole-room impact at normal play distance; a technically correct millimetre-scale bevel is not proof that material fidelity or atmospheric lighting meets the reference.

For lighting artifacts, make paused, fixed-view comparisons that isolate direct shadows,
contact occlusion, diffuse transport and specular reflections independently. A toggle that
changes several contributions cannot attribute an artifact to just one. Keep capture
boundary conditions unchanged by comparison controls, restore normal rendering afterward,
and retain failed hypotheses alongside screenshots. Normalizing nearly-zero visibility
weights can amplify a filtered shadow into a hard boundary; inspect low-coverage behavior
separately from sampler capacity, shader compilation and nominal interpolation tests.

### Draft versus resident verification

For editors that preserve a separate playable snapshot, verify the active version actually
contains the edited entities before judging rendered output. A saved editor draft is not
evidence that an existing resident simulation was upgraded. Apply through the normal user
operation, verify persistent character/content migration, then resume real interactions.
Record camera, clock and cutaway differences when comparing images; do not call those a
controlled lighting A/B. Preserve failed observations rather than attributing unchanged
output to the new implementation prematurely.

When an apparent download/action failure opens an unrelated panel, verify the target's
actual hit-test element at its bounding-box centre before blaming download APIs. A visible
accessible button can be occluded by another control. Record target rectangle, topmost
hit element and viewport, fix layout/stacking, then verify the original public action and
its actual artifact. A successful click command alone is not evidence of the intended action.
