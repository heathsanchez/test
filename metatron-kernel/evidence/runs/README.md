# External qualification runs

GitHub Actions workflow `Metatron Kernel Genesis G2` emits one immutable
artifact named `metatron-kernel-genesis-g2-<candidate-sha>` per branch head.
The artifact contains:

- `qualification.json`: deterministic verdicts for the frozen six-case G2
  cohort and the exact candidate/Arena SHAs;
- `instructions.json`: `perf instructions:u` for the same ordered cohort, or
  an explicit `unavailable` result when the runner exposes no PMU;
- `attestation.json`: the workflow run ID, job ID, authority SHAs, verdict
  summary, and instruction record.

Only `status: measured` records from the same metric, runner class, cohort,
case order, Arena SHA, and build profile are eligible for performance
comparison. An unavailable local or hosted-runner PMU may reject promotion but
cannot be replaced with wall time, Callgrind, or a different cohort.

Artifacts remain external evidence rather than copied into this directory.
The machine-readable experiment ledger records the inspected run and artifact
IDs after qualification.
