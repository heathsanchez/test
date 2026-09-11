# Verified Meta-Developmental Compounding V1 Results

## Terminal verdict

**VERIFIED META-DEVELOPMENTAL COMPOUNDING — bounded, exhaustive, causal.**

Retaining the acquired `D1` developer reduced the fully charged cost of acquiring the different `D2` developer. Retaining both `D1` and `D2` then reduced acquisition of `D3` further. Neither earlier developer directly solved its later target.

## Primary verifier-call results

| Acquisition | Cold | Partial developmental state | Full warm | Ablation |
|---|---:|---:|---:|---:|
| `D2` joint-coordinate cover | 37,234 | — | `D1`: 1,408 | 37,234 |
| `D3` temporal joint cover | 222,808 | `D1`: 7,226 | `D1+D2`: 210 | 7,226 |

- Aggregate cold: **260,042** calls.
- Aggregate full warm: **1,618** calls.
- Aggregate reduction: **160.718×**.
- Warm next-acquisition curve: **1,408 → 210** calls.
- `D2` search depth: **6 cold → 3 warm**.
- `D3` search depth: **7 cold → 4 with D1 → 2 with D1+D2**.

All internal verifier probes inside retained macros were charged. Search was level-complete: every program at the first successful description length was evaluated, eliminating within-level enumeration-order advantage.

## Controls

| Acquisition | Warm | Sham | Answer memory |
|---|---:|---:|---:|
| `D2` | 1,408 | 83,086 | 246,970 |
| `D3` | 210 | 1,399,752 | 2,181,120 |

Removal of `D1` restored the exact `D2` cold cost. Removal of `D2` restored the exact `D1`-only `D3` cost. Matched inert macros and earlier selected-coordinate memories did not reproduce the gain.

`D1` alone failed `D2`; `D2` alone failed `D3` without temporal lifting. The retained procedures therefore reduced acquisition cost without containing the later answer.

All 11 precommitted gates passed, with no correctness regression.

## Exact claim earned

In this frozen finite program language, an acquired developmental procedure made acquisition of a distinct later developmental procedure cheaper, and accumulating the second acquired procedure made the next developmental acquisition cheaper still. Causal removal restored the corresponding earlier costs, while matched sham state and answer memory failed.

Classification: **EXHAUSTIVE** over the declared bounded program search; **BOUNDED-CAUSAL** under removal; **VERIFIED META-DEVELOPMENTAL COMPOUNDING** for this curriculum; **PROVED** only for the Lean typed retention/preservation facts.

## Boundary

The effect is description-language compounding through verified reusable macros in a synthetic finite program domain. It does not establish cross-domain compounding, unbounded improvement, model learning, or primitive-substrate genesis. The magnitude should not be generalized beyond this frozen search grammar.

The most consequential residual is whether the same second-order cost curve survives a prospective cross-domain developmental curriculum where useful procedure overlap is not built into a shared token grammar.

## Invalid implementation run

Run 34601054459 / job 103268165090 is an **INVALID IMPLEMENTATION FAILURE**, not scientific evidence. Pipefail exposed an indexed Lean residual elaboration defect; it was repaired before the authoritative run.
