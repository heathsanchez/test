# Results

Status: **VERIFIED_EXPERIMENT_META_SUBSTRATE_GENESIS**.

The complete old closure contained all 16 stateless Boolean maps and none
separated the two histories with identical present inputs. Exhaustive generic
two-state-table construction found a stateful separator after 10 charged
candidates, producing observations `(0,1)`.

All proof, novelty, anti-escalation, stale-certificate, inert-state, and
ablation gates passed. Fully charged cost was 34,659 against 50,000 passive,
for 15,341 saved calls.

Scientific workflow: https://github.com/heathsanchez/test/actions/runs/34682784242

Job: https://github.com/heathsanchez/test/actions/runs/34682784242/job/103524385216

Artifact: 10293399981 (`sha256:acfad65c309876fa6d2c50da21b4457ed4d3fee2c4d6b77d1810437e4522b1b2`)

The preceding run 34682737945 is invalid infrastructure: Python passed, but
Lean rejected the data-carrying completeness witness's universe placement.
Only that proof encoding was corrected before the valid run.
