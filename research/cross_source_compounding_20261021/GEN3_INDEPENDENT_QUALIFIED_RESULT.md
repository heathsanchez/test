# Gen3 independent reproduction and corrected ablation — 2026-10-21

## Authority
- Pinned subject: `go-ini/ini@e2db55b0e088fa4ee0c128aa4ade263cdc1d7f08`.
- Independent original run [39540300278](https://github.com/heathsanchez/test/actions/runs/39540300278) passed native reproduction, but **cold ablation was INVALID**: it included the previously known witness directly, yielding an artificial one-probe advantage. Preserve as a rejected ablation, not scientific evidence.
- Corrected exact-source run [39540390818](https://github.com/heathsanchez/test/actions/runs/39540390818), job 119026529325, **SUCCESS**; retained artifact [12318748473](https://github.com/heathsanchez/test/actions/runs/39540390818/artifacts/12318748473), SHA256 `f314c0678618af7d69b97faf3bf308793a8e2dde2730c3a685acae3046edd0c3`.

## Verified bounded behavior
Independent literal test on original pinned source:
- input `"plain\\"`, first serialized byte sequence `5b6d61696e5d0a56616c7565203d20706c61696e5c0a`;
- second serialized byte sequence `5b6d61696e5d0a56616c7565203d20706c61696e0a`;
- recovered value `"plain"`, losing trailing backslash;
- ordinary negative control input `"plain"` retained `"plain"`, with matching first and second bytes.

## Corrected comparative causal probe
All four arms used the same original Go verifier and fixed mutation grammar, and identified the same counterexample:
| Arm | Native probes | Measured inner-loop time |
| --- | ---: | ---: |
| retained Gen1 seeds / warm | 12 | 296,945 ns |
| cold ablated (only primitive `plain`, same grammar) | 12 | 303,578 ns |
| equal-information comparator (same seeds and grammar) | 12 | 157,645 ns |
| restored | 12 | 147,987 ns |

The one-shot nanosecond durations reflect native in-process execution and order/cache noise; they are not lifecycle costs. Probe counts TIE and no causal advantage is found. The comparator even has lower observed time, but not a reproducible speed claim.

## Promotion decision
- **WARRANTED_BOUNDED:** source-native independently implemented reproduction of a trailing-backslash serialization failure and the exact first/second encoded byte difference.
- **REJECTED for this fixture:** retained-seed discovery reduces native candidate probes against equal-information conventional alternatives; all arms needed 12.
- **UNKNOWN:** general INI bug classification, broader grammar semantics, new independently invented method, source-distinct second-order compounding, end-to-end economic gain.
- **NOT MEASURED:** human method design, adapter construction, source qualification, failed attempts, cold process restart and future reuse economics.

The initial compromised ablation is SUPERSEDED by corrected run, while retained as negative methodological evidence. No third-party repo mutations or external outreach.
