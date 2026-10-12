# Execution and evidence boundaries

`run-adapter` executes the explicitly supplied argv with the host user's privileges and inherited environment. It is not a sandbox. Review adapters, dependencies and build hooks before execution; use an isolated environment and disposable data where appropriate. A dedicated run directory does not restrict filesystem/network access, and logs can consume disk space.

`check`, `audit` and `plan` read records; they do not execute commands embedded in evidence. Hashes detect drift relative to recorded metadata. They do not authenticate provenance, prove execution, or resist an actor who can rewrite evidence and its records. Keep reviewed evidence snapshots in controlled storage if your project requires stronger guarantees.

Do not publish secrets, source binaries or private captures in issue reports. Report reproducible defects with minimal synthetic inputs. This repository does not currently advertise a dedicated private security-reporting channel or response SLA.
