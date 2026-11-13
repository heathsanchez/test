# C128: original N7 direct type-proof versus expensive fallback owners

Status: **WARRANTED_BOUNDED diagnostic** on the C105-derived surrogate;
standard-budget N7 remains UNKNOWN. 2026-11-14 NZDT.

## Authorities

Frozen upstream Arena artifact `11272848230` and original unchanged
`good/perf/magma-list-pair-n7.ndjson` SHA256
`abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`.
Configuration: `NUCLEUS_EXPERIMENTAL_RELEVANCE=1` and
`NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR=1`; original standard 65,536 versus
diagnostic 14,155,776 steps. Each run executed with observer OFF and ON;
exit status and stdout were identical. No semantic source, checker rule or
fuel budget was changed. Native [green run #43483269811](https://github.com/heathsanchez/test/actions/runs/43483269811),
[uploaded native C128 JSON](https://github.com/heathsanchez/test/actions/runs/43483269811/artifacts/14065354327),
artifact ZIP SHA256 `6619a0435882c1a1afebc2209d5acc3dcc97465db772c4b2aebde60d3aeaf67a`.
Source commit on isolated remote branch `research/nucleus-c125-c105-surrogate-ci-20261114`:
`78a3db3f1a905b350874f8170509d9de683412c1`.

## Bounded observation

| Measured observation | Standard 65,536 | Diagnostic 14,155,776 |
| --- | ---: | ---: |
| Original N7 verdict | UNKNOWN | ACCEPT |
| Source App 8835 function Expr 8805 Pi head | UNKNOWN | PROVEN |
| Outer charged work at App 8835 | 203 | 203 |
| C95 phase receipts | 2 | 0 |
| C96 demanded-major owners | 2 | 0 |
| C97 replay owners | 2 | 0 |
| C97 largest owner charge | 65,250 | 0 (no owner) |
| C97 repeated node+env counts summed over owners | 42,075 | 0 (no owner) |
| C97 repeated head+pending counts summed over owners | 38,973 | 0 (no owner) |
| Recorded nested replay failure lines | 26 | 26 |

The two low-budget C97 owner receipts are:

```
start=65250 spent=65250 major_work=41958 loops=40538
  unique_node_env=12828 repeat_node_env=27710
  unique_head_pending=14715 repeat_head_pending=25823
start=32625 spent=32624 major_work=25147 loops=24413
  unique_node_env=10048 repeat_node_env=14365
  unique_head_pending=11263 repeat_head_pending=13150
```

Their costs and repeated-state counts **cannot be added as independent work**:
the owners may overlap or nest. These diagnostic equality keys do not establish
typed context/binder/level/pending-source equivalence. The first 32 printed
low-budget `Decidable.rec` iota records repeatedly show registered source RHS
`ExprId(531)` under constructor `Decidable.isTrue` (`NameId(146)`), but this is
only a *sample*; same RHS source expression does not imply identical captured
arguments or final values. Both arms print 26 nested failures, including
`projection-constructor-mismatch` probes; such a failure is not itself the
terminal verdict when the high arm ACCEPTs.

## Decision / cheapest next test

High-budget success **avoids the fallback owners**. Thus accelerating a
fallback replay alone is not yet evidence of a standard-budget ACCEPT. The
first target is the *direct source-checked path* producing the Pi type at
14,155,776: instrument the smallest earlier successful typed reduction that
is absent/UNKNOWN at 65,536, with exact captured frame, universe substitution,
source constructor/rule and its own budget/charge. Determine whether its work
is repeated and certifiably shareable in a single owner, or whether a new
structural evaluator is required. Do not infer success from two repeated source
IDs or count-only keys; never convert UNKNOWN into a rigid-equality proof.

C128 is **not** exact C124/C125b lineage: original historical C106–C108
objects are still unavailable. It does not rerun the protected 403-case or
forged matrix, and closes none of the six original valid standard UNKNOWNs.
