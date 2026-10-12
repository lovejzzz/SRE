# First application: PZ inventory → web / couch co-op

This is a research plan, not a completed source-runtime experiment. Obtain the installed path/version from the current user/environment; do not assume a contributor's machine path or package version. Keep original assets/code and saves out of public repositories.

Start with readable inventory UI and timed-action Lua, then inspect Java inventory classes as needed. Useful investigation targets include `ISInventoryTransferAction.lua`, `ISInventoryTransferUtil.lua`, `ISInventoryPane.lua`, `ItemContainer`, and `InventoryItem`. Public modding API docs may not match the installed build. Fingerprint the actual artifacts.

Candidate questions: source membership; same-container rejection; capacity at exact boundaries; nested containers and cycles; effective encumbrance versus raw mass; equipped bags; favorite protection; individual identity versus UI grouping; cancel/partial transfers; persistence; two actors requesting one shared item. Treat these as hypotheses until confirmed on the pinned version.

Use a small isolated test world and a test mod/adapter when available. Fixture setup can spawn items; a transfer under test must use the real timed-action path. Record identity, parent container, counts, weight inputs, equipment, result, and action lifecycle. Do not bypass transfer semantics with direct remove/add calls and report the result as game behavior.

Separate preserved inventory rules from designed couch-co-op conflict handling and target UI. A browser prototype with immediate moves and invented reduction factors demonstrates original logic; it is not source fidelity. Dual gamepads, disconnect/reconnect, per-player focus, save recovery, and actual TV resource use are separate destination obligations.

First successful milestone: one real source scenario, an independent successor implementation, matching normalized traces, an intentional faulty successor detected by comparison, and a destination interaction test. Expand only after this path works; keep the full requested scope in the project contract.
