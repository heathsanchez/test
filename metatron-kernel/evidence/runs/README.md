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

## Inspected runs

| Candidate | Run / job | Artifact | Correctness | Instructions |
| --- | --- | --- | --- | --- |
| `47aff936001f88204f2bf05a9fad9abe4eda9a9c` | `35620658852` / `106402590918` | `10648885370`, digest `c100e632...9176` | 6 matched; 0 incomplete, incorrect, or error | `UNKNOWN`: PMU unavailable; no same-cohort control |
| `8a204d7727eb686139997cf299b93d75db9adf8c` | `35677667353` / `106587470554` | `10673617458`, digest `e8528357...8b0f` | 6 contract + 41 tutorial matched; G14 oracle 41 equal, 0 delta, 0 mismatch | `UNKNOWN`: PMU unavailable; no same-cohort control |

The successful run is available at
<https://github.com/heathsanchez/test/actions/runs/35620658852>. Its correctness
attestation is retained. Its performance record is deliberately not eligible
for promotion.

The G15 run is available at
<https://github.com/heathsanchez/test/actions/runs/35677667353>. It additionally
replayed every G12-G14 exact/perturbed vector against sealed head `d128565e...`
and protected tutorial 042 as `UNKNOWN` in both arms. No retired-instruction
promotion is claimed.
