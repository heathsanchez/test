# Collatz Flash propagation fixture

## Result and scope

This retrospective fixture executes eight distinct bank-order policies on the
same frozen 162-source cohort. It tests the effect of releasing a manually
reviewed dominance rule after the first completed job. It is not autonomous
theorem discovery, an asynchronous distributed implementation, or a new holdout.

| Arm | Policies executed | Policies blocked | Actual T calls |
|---|---:|---:|---:|
| Isolated | 8 | 0 | 1501097 |
| Passive shared memory | 8 | 0 | 1501097 |
| Flash propagation | 1 | 7 | 208613 |
| Propagation ablation | 8 | 0 | 1501097 |
| Upfront rule guard | 0 | 8 | 17401 |

Three fresh-process repetitions per arm reproduced deterministic outputs.
Local median process times were approximately 0.829, 0.822, 0.148, 0.826,
and 0.051 seconds respectively. These short local timings are descriptive,
not stable platform benchmarks. CI regenerates its own timings.

T calls include endpoint validation, macro replay, in-run certificate checking,
and a second certificate/budget check. Thus they differ from the earlier
macro qualification's narrower cost metric. Common setup is included in every
arm. Full subprocess elapsed time additionally charges imports, bank validation,
policy sealing, graph matching, event recording and output serialization.
Initial human discovery/review of the supplied rule and original bank acquisition
are sunk costs, excluded equally. No new capability composition or quotient
construction is performed; no costs for those operations are claimed.

## Authority and graph

The graph has a rule-to-job dependency. The reviewed conditional argument is
documented in `collatz-macro-qualification-v1.md`: any successful stepwise replay
certificate is reached by direct iteration within its preparation-plus-replay
allowance. Changing the bank order cannot evade this argument. Blocking concerns
the claim of strict advantage in counted T steps, not certificate validity.

Admission is explicitly a trusted, manually reviewed rule allowlist, not a Lean
or general proof checker. A finite benchmark cannot establish that universal
argument. The result event merely releases a rule already supplied to this
fixture; it does not discover it. The report hashes the rule document, and the
git commit pins the runner and authority implementations. Contracts are produced
internally for this fixed runner; they are not authenticated arbitrary plugins.

Propagation matches the entire declared contract and records the supporting
dependency. Symbolic execution and wall-time claims are outside the rule's
scope. Revocation reopens dependent blocked jobs; completed jobs remain completed.
Regression tests cover these boundaries and rejection of an unknown authority.

The shared-memory arm deliberately stores evidence without querying it at
dispatch. Ablation removes the propagation edge and is therefore equivalent to
that passive control. The stronger upfront guard does query before dispatch.
It blocks all eight jobs and beats delayed Flash. The remaining 17401 T calls
are common endpoint-validation overhead, which a production preflight guard
could also avoid by running before data loading.

## Consequence

Propagation removes redundant work relative to passive storage in this fixture.
It demonstrates no benefit over an applicable upfront guard. The useful design
requirement is to apply admitted consequences at dispatch and when new evidence
arrives. A later experiment must introduce genuinely new evidence during live
work and compare against an equally competent scheduler, including cancellation
and invalidation costs. The present result does not establish cross-domain
synergy, general Flash superiority, or Collatz termination.

Protected S_k, 119/104, and departure-countdown evidence is unchanged. The
previous macro performance rejection remains valid.

## Reproduction

```
python -m unittest discover -s experiments -p test_collatz_flash.py -v
python experiments/collatz_flash.py --output /tmp/collatz-flash
```

CI green means the scoped propagation and controls reproduced. Its verdict
explicitly includes `NO_ADVANTAGE_OVER_UPFRONT_GUARD`.
