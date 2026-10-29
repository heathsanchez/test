# Historical capability cold transport — bounded source replay v0

Selected before source inspection from the canonical 70-row capability index:
the first documented `WARRANTED_BOUNDED`, not explicitly runtime-integrated,
Python `.py` implementation with a machine-visible reusable function and
an original external verifier. This selects `webarena-e-f-causal-composition`,
source `heathsanchez/test@32e2e8f21d642001323237e31fbe7bea01cb975e`.

Two separate checks:

1. `cold_call.py`: a source- and dependency-hash-pinned **generic Python
   callable** executes the original `select_winners` function in a fresh
   process on the historical independently source-observed WebArena rows.
   Source tampering, dependency tampering, and unexported symbols fail closed.
   This is an untyped prototype: imports run with current process permissions;
   it is NOT a sandbox, typed MGSO, Metatron admission, proof or external grant.
2. `qualification.py`: independently re-evaluates **27 archived responses**
   against the original `ServiceNow/webarena-verified@6473f72` scorer and then
   reruns all five original E+F candidate-search arms, including two later task
   responses per arm, on **archived** source observations. The task-290 SKU
   evidence comes from the original archived browser observation, not a new
   live browser observation. No oracle/reference answers enter candidate search.

Authoritative archived inputs are GitHub Actions artifacts `11467591099`,
`11663621950`, and `11665265299`. Their ZIP SHA-256s and exact source pins
are checked in the workflow and `qualification.py`. Reproduction is the
`capability_cold_transport_v0.yml` GitHub Actions workflow on the isolated
research branch. On local checkout, unzip the composition archive to
`historical_composition/`, install the pinned original verifier into an
isolated environment, then run:

```bash
python -m unittest discover -s cold_capability_probe -p 'test_*.py' -v
python -m cold_capability_probe.qualification --out cold_capability_probe/output
```

## Expected bounded result

| Arm | Native candidate evaluations | Tasks 292+290 from archived source |
| --- | ---: | --- |
| Retain E+F | 1 | Both pass |
| Remove E | 3 | Both pass |
| Remove F | 3 | Both pass |
| Remove both | 9 | Both pass |
| Equally informed stateless | **1** | Both pass |

**WARRANTED only for the exact historical pinned source/archive replay**, once
the independent replay command passes. Relative candidate-search savings
against weak ablations coexist with **TIE** against the strongest stateless
baseline. Typed `.mg`/MGSO promotion, automatic Metatron activation, true
prospective new-source G2/G3 discovery, and lifetime positive economics remain
**UNKNOWN**. Do not convert this archival result into a fresh-task result.
