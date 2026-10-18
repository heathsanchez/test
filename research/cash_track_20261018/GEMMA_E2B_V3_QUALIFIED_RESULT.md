# Gemma 4 E2B V3: independently qualified non-thinking inference, native repair refused
Date: 2026-10-18 (NZ).

## Objective / result

**WARRANTED_BOUNDED_NONTHINKING_FINAL_OUTPUT; MODEL_REPAIR_NOT_ADMITTED.**

A new, separately preregistered, single-run Gemma 4 E2B CPU test changed **only** llama.cpp server mode to `--reasoning off` while preserving the V2 1024 completion-token cap, original exact Go source and existing native oracle. The model emitted actual final text and stopped normally after 88 tokens instead of spending the whole completion allowance in `reasoning_content`. However, the raw response **began with a Markdown code fence**, violating the frozen JSON-only contract, and proposed changing the *basic check-failure regex* instead of the exact *declared-outage* regex. No generated source edit was applied or tested. GitHub CI GREEN is evidence of the experiment's execution and correct refusal, **not a successful automated repair**.

## Exact source and model authority

- V3 isolated branch: [research/gemma4-e2b-nonthinking-v3-20261018](https://github.com/heathsanchez/test/tree/research/gemma4-e2b-nonthinking-v3-20261018), **no PR and no old V1/V2 retesting**.
- Protocol frozen first at [commit 766b8688](https://github.com/heathsanchez/test/commit/766b8688cc869b63df391d6f03aab96241fc287a), source-only V3 runner [c530c08d](https://github.com/heathsanchez/test/commit/c530c08dd21a256d6aea14fcce12508303daa5ee), corrected workflow-qualified exact head [ffe7a6fc](https://github.com/heathsanchez/test/commit/ffe7a6fc8e4355404e5fc1446a66c881e46b750c).
- Independently green [GitHub Actions #39099572362](https://github.com/heathsanchez/test/actions/runs/39099572362), native job `once-cpu-gemma-native`. [Original artifact #12125803921](https://github.com/heathsanchez/test/actions/runs/39099572362/artifacts/12125803921) was downloaded and independently rehashed/opened. **ZIP SHA-256 `cb0bc2b875dbcb2c18d5f431d635d01cbb399e52b8a49c8bd36be8b20eff908f`** exactly matches GitHub provider report; contains native Go baseline log, exact prompt, raw model response, immutable protocol, server log/help, metric JSON, pinned tool and model source revisions.
- Same GGUF `ggml-org/gemma-4-E2B-it-GGUF`, `gemma-4-E2B-it-Q4_0.gguf`, source revision `b4243c156154b6dca9324415f8c7ccc098b4aed1`; model file SHA-256 `8e30dff3ac4c8434c49a7036fa15564bdbb6044e42bf04550bf1a096ad7e6a52` checked inside CI before inference. Same pinned llama.cpp `b11433` / `50569eb87df530daff11afda229ceb9ab8e6cae8`, server mode `--reasoning off`, 4 CPU threads, 4096-token context, seed 181026, temperature 0, max_tokens 1024. No RunPod or metered API.
- Source base `OllyInsurance/fern-platform@ee843f4babd4c05e819aa86701e409b58e328c66`, source file SHA256 `976be45f6d65a8892e0fba94294fda0c68ac05be71b3cc6c73f31648aaad9ca2`, prompt SHA256 `f7bf130560fe2ba7370e8c99ce45d4584b6f6a3d37e33a399a41fb2a255061d2` exactly equal to V2 frozen identities. Frozen Go test fixture SHA256 `11852940f6f9796c8c895688077e5467ed3c92f0c8c033405c59a046a045b8a6`.

## Actual observed result

| Measurement | V2 thinking | V3 non-thinking |
|---|---:|---:|
| Prompt SHA / original Go code | same | same |
| Server config | default thinking | `--reasoning off` |
| Completion cap | 1024 | 1024 |
| Completion tokens consumed | 1024 | **88** |
| Reasoning-content chars | ~4211 | **0** |
| Final content chars | 0 | **321** |
| Finish reason | `length` | **`stop`** |
| Model inference wall | 115.983 s | **54.324 s** |
| JSON-only contract | REJECTED | **REJECTED_CODE_FENCE** |
| Source-bound generated edit | NOT_RUN | **NOT_RUN** |
| Original Go named tests | 6 PASS / 1 FAIL | **6 PASS / 1 FAIL** |

Actual V3 model text, preserved unmodified in the archive:

```json
{
  "old_regex": "CHECK FAIL\\b",
  "new_regex": "(?i)CHECK FAIL\\b",
  "claim": "The change modifies the check for 'CHECK FAIL' lines to be case-insensitive, ensuring that the logic in `envFault` correctly identifies check failures regardless of case, which is a minimal safe change to improve robustness."
}
```

The independent frozen source's actual declared-outage matcher is `CHECK FAIL\b[^\n]* DURING DECLARED OUTAGE \S+`, not `CHECK FAIL\b`. Even a *posthoc* Markdown fence removal would not satisfy the exact `old_regex` binding. The separate generic `reCheckFail` variable does contain `CHECK FAIL\b` but changing it is **out of scope** for this protocol. Thus both response formatting and target selection were wrong; no manual repair of either is counted.

Actual original Go subtests executed: 7 named cases; all protected negative controls passed; `step_declared_only` retained the expected FAIL; Go process returned 1. Source identity and unchanged fixture were checked.

**Cost accounting:** 54.324 seconds is **model generation time**, not model download/build/preflight/native setup. V3 runner's total measured `wall_seconds = 134.94` covers actual script work including original native Go execution but **excludes the workflow's llama.cpp build/model download**; no claim of full lifetime cost savings vs matched baseline. V2 inference was measured under thinking mode; nonthinking reduction is one paired observation only.

## Failure / apparatus lineage and stop decision

1. Initial [workflow #39099436120](https://github.com/heathsanchez/test/actions/runs/39099436120) was GitHub YAML validation RED, **0 jobs/no model** due plain-scalar quoting of `ci: ` inside job `if`.
2. [Apparatus note](https://github.com/heathsanchez/test/blob/research/gemma4-e2b-nonthinking-v3-20261018/research/cash_track_20261018/GEMMA_E2B_V3_WORKFLOW_APPARATUS_RED.md) was frozen before a **single quote-only correction**; the interim invalid workflow produced another RED #39099558663 with 0 jobs. Neither counts as an inference.
3. Exact frozen protocol was actually executed in [GREEN #39099572362](https://github.com/heathsanchez/test/actions/runs/39099572362) at qualified commit `ffe7a6fc`. A later evidence-only commit does not rerun: workflow path filter covers only runner/workflow and job `if` admits only the exact command message.

**Promotion:** nonthinking final-output obstruction RESOLVED in this one bounded experiment. **REJECTED:** this sampled model answer under the exact output/source contract. **UNKNOWN:** whether the model could produce a valid repair under a different constrained-format or task interface, unbounded performance, generalization, matched-agent advantage, competitive superiority. **NO claim:** successful Gemma developer agent, hidden benchmark victory, autonomous new method, open-ended G2, Kaggle entry, accepted source patch.

**First next causal experiment if separately frozen:** constrained JSON emission with the *same model/input* and independently check source target binding and native repair under untouched tests; do not silently peel code fences, change task wording, switch model weights or retune after seeing output. Current V3 declared **one-shot STOP** and executed it.
