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
| `865548098d16588db5aef79b9e094746933497d9` | `35686513640` / `106614391496` | `10676299174`, digest `fbb4091c...5106` | 6 contract + 42 tutorial matched; G15 oracle 41 equal, 1 earned delta, 0 mismatch | `UNKNOWN`: PMU unavailable; no same-cohort control |
| `ebc901d24688d2aa672c38e4fd80e20d6a0e5b15` | `35687371672` / `106616975935` | `10676794003`, digest `dc5a59be...89d2` | 6 contract + 43 tutorial matched; G16 oracle 42 equal, 1 earned delta, 0 mismatch | `UNKNOWN`: PMU unavailable; no same-cohort control |

The successful run is available at
<https://github.com/heathsanchez/test/actions/runs/35620658852>. Its correctness
attestation is retained. Its performance record is deliberately not eligible
for promotion.

The G15 run is available at
<https://github.com/heathsanchez/test/actions/runs/35677667353>. It additionally
replayed every G12-G14 exact/perturbed vector against sealed head `d128565e...`
and protected tutorial 042 as `UNKNOWN` in both arms. No retired-instruction
promotion is claimed.

The G16 run is available at
<https://github.com/heathsanchez/test/actions/runs/35686513640>. Exact tutorial 042
is the sole earned oracle delta: frozen G15 returns `UNKNOWN`, while the retained
PUnit law returns `ACCEPT`; tutorials 001–041 are equal and the malformed/broader
PUnit falsifiers preserve their required REJECT/UNKNOWN boundaries. No
retired-instruction promotion is claimed.

The G17 run is available at
<https://github.com/heathsanchez/test/actions/runs/35687371672>. Exact tutorial 043
is the sole earned oracle delta: sealed G16 returns `UNKNOWN`, while the retained
Eq index law returns `ACCEPT`; tutorials 001–042 are equal and malformed/broader
Eq falsifiers preserve their required REJECT/UNKNOWN boundaries. No
retired-instruction promotion is claimed.
