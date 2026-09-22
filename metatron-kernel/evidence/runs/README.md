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
| `bb7809104681852b46d71c688814f24692965b1b` | `35704232366` / `106669198325` | `10682964232`, digest `f3f7ae1d...781b` | 6 contract + 44 tutorial matched; G17 oracle 43 equal, 1 earned REJECT→ACCEPT delta, 0 mismatch | `UNKNOWN`: PMU unavailable; no same-cohort control |
| `60fde2527b7a57c14487b7930d6083451dd01aeb` | `35707420135` / `106679605077` | `10684434897`, digest `1b69b0ef...e86a` | 6 contract + 45 tutorial matched; G18 oracle 44 equal, 1 earned UNKNOWN→ACCEPT delta, 0 mismatch | `UNKNOWN`: PMU unavailable; no same-cohort control |
| `97ae436b2af00d563a5460d01d3839d97304b5b0` | `35761375025` / `106859961966` | `10710223928`, digest `e2101190...556b` | 6 contract + 49 tutorial matched; G19 oracle 46 equal, 3 earned UNKNOWN→REJECT deltas, 0 mismatch | `UNKNOWN`: PMU unavailable; no same-cohort control |
| `1423040508c602c628f92e845d4ccc3796f165ba` | `35763602005` / `106867429092` | `10711556671`, digest `d80d8c82...2209` | 6 contract + 53 tutorial matched; G20 oracle 49 equal, 4 earned UNKNOWN→REJECT deltas, 0 mismatch | `UNKNOWN`: PMU unavailable; no same-cohort control |

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

The G18 run is available at
<https://github.com/heathsanchez/test/actions/runs/35704232366>. Exact tutorial 044
is the sole earned oracle delta: sealed G17 returns `REJECT` on the valid Nat
fixture, while G18 returns `ACCEPT`; tutorials 001–043 are equal and the
malformed/broader Nat falsifiers preserve the required REJECT/UNKNOWN boundaries.
No retired-instruction promotion is claimed.

The G19 run is available at
<https://github.com/heathsanchez/test/actions/runs/35707420135>. Exact tutorial 045
is the sole earned oracle delta: sealed G18 returns `UNKNOWN`, while the composed
RBTree law returns `ACCEPT`; tutorials 001–044 are equal, full recursor/rule
falsifiers pass, and broader RBTree neighbours remain outside authority. No
retired-instruction promotion is claimed.

The G20 run is available at
<https://github.com/heathsanchez/test/actions/runs/35761375025>. Tutorials 046,
047, and 049 are the three earned `UNKNOWN → REJECT` deltas against sealed G19;
048 is an equal `REJECT` control. Tutorials 001–045 remain unchanged. The
diagnostic suffix atlas moves the first mismatch to tutorial 050. No
retired-instruction promotion is claimed.

The G21 run is available at
<https://github.com/heathsanchez/test/actions/runs/35763602005>. Tutorials 050–053
are the four earned `UNKNOWN → REJECT` deltas against sealed G20; tutorials
001–049 remain unchanged and conversion-sensitive tutorial 055 remains outside
G21 authority. The suffix atlas moves the first mismatch to tutorial 054.
