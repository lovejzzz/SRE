# Any software, chosen platforms, explicit tradeoffs

The product ambition is broad; platform feasibility is an experiment, not a guarantee. Build a capability map before architecture choices: CPU/ABI, GPU/API, memory/storage, input, display, filesystem, networking, background execution, permissions, dependencies, and distribution constraints. Pin the target OS/runtime/device. Host performance is not a measurement of the target.

Separate portable domain behavior, platform services, UI/input, persistence, and external service adapters. Choose a language/framework based on the destination and original workload; do not impose one engine on a CLI, desktop editor, TV game, and mobile app. Reuse a portable library when license and behavior fit; otherwise reimplement behind an explicit contract.

For each platform adaptation specify: original behavior; platform limitation; intended replacement; compatibility/data migration consequences; how the user will recognize success; target test. If a capability cannot exist on the destination (for example an unavailable driver or inaccessible remote service), surface the dependency and propose an explicit alternative. Do not silently replace local execution with streaming or a paid API.

For enhancements specify before/after behavior, interaction with preserved features, failure modes, and measurable acceptance criteria. Test the enhancement independently, then regress preserved behavior. Planned differences belong in the contract before comparison; never conceal them with broad comparator exclusions.

Measure resource budgets on representative workloads: frame-time distributions, memory peaks, startup latency, data durability, accessibility and input latency as appropriate. Use the user's budgets, or label provisional targets as assumptions. Deliver portable build instructions and explain any platform whose artifacts or hardware tests could not be produced in the available environment.
