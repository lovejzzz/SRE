# Research tooling and REA

Select tools by the artifact and question. Inspect source and readable scripts first. Use static analysis to propose behavior, and runtime observations to test it. A decompiler listing can be incomplete or misleading; preserve uncertainty and original offsets/symbols.

| Artifact | Useful investigation | Additional work SRE owns |
| --- | --- | --- |
| Source repository | language tooling, call graphs, tests, dependencies | build reproducibility, behavior contract, independent implementation |
| Native executable | REA with supported native backend | test harness, environment, state extraction, target rewrite |
| JS/Electron or .NET | REA-supported artifact analysis, language tools | runtime semantics and packaging on the destination |
| Android APK | inspect current REA Android capabilities or appropriate Android tools | device execution, input/output adapters, portable domain model |
| Desktop Java JAR / Lua | language-specific inspection/decompilation; directly read Lua | custom instrumentation and game-specific semantics |
| Website or service client | accessible UI/network observations and public contracts | distinguish observable client behavior from unavailable server logic |

REA is optional. Discover available tools using the host's tool catalog; inspect the current input schema and prerequisites before invoking. In an MCP client, `tools/list` is the protocol-level discovery source, not a shell command. Record REA version/commit, backend, session ID, evidence references, and limits. Do not hard-code a remembered catalog into the orchestrator.

Upstream documentation describes evidence/session and process-capture facilities; confirm availability at runtime. A process capture of files/logs/exit status does not automatically supply application state or semantic equivalence. SRE supplies scenario reset, action execution, state extraction, normalization, comparison, and acceptance. If upstream coverage/obligation utilities fit the actual schema, reuse them; do not assume their names prove they solve this layer.

Authoritative starting points (reviewed 2026-10-12; may change):
- [REA repository](https://github.com/morluto/rea)
- [MCP contracts](https://github.com/morluto/rea/blob/main/docs/mcp-contracts.md)
- [Process capture](https://github.com/morluto/rea/blob/main/docs/process-capture.md)

Record evidence as: claim; source URI/file plus hash/version and locator; observed/static/hypothesis/design classification; experiment inputs; actual result; confidence/limitations; dependent feature IDs. The same model-generated statement repeated twice is not independent evidence.

Do not bundle REA or auto-install its engines just to activate this skill. Use existing integrations where possible; select and install dependencies only when the current task requires them and existing authorization covers the action.
