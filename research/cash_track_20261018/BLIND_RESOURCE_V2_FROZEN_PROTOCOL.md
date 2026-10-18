# 2026-10-18 — Frozen V2 evaluator leakage falsifier + matched exact-information comparator

**Objective:** repair the original publicly archived seven-case packet dataset into an actual *agent-facing* resource without answer disclosure. Preserve old evidence. This is a benchmark design defect, not a new defect in any original upstream software.

## Original immutable authority
- Historical construction [GREEN #39087636547](https://github.com/heathsanchez/test/actions/runs/39087636547), artifact [#12121047787](https://github.com/heathsanchez/test/actions/runs/39087636547/artifacts/12121047787), source [original code](https://github.com/heathsanchez/test/blob/94353fbc835fa562ec377bca9ba0a300da22f500/research/cash_track_20261018/runner.py).
- Seven historical cases; one true scoped original + seven hand-constructed invalid mutants each = 56. Original file `evidence_cases.jsonl` exposes `admissible`, `control`, `id`, `source_case`, `packet`. Thus it must **never** be handed to a model as an inference-only blind test.
- Independently loaded original ZIP in a local read-only Python test on 18 Oct: three classifiers `row['admissible']`, `row['control']=='original_scoped'`, and `row['id'].endswith('::original_scoped')` individually achieved **56/56** while **reading no evidence packet**. This is a **WARRANTED_BOUNDED corpus label-leakage counterexample**, not a measured model performance result.

## Predeclared V2 repair
1. Keep legacy `evidence_cases.jsonl` unchanged for backwards-compatible transparent demonstrations; mark **labeled/train-only**. Do not relabel historical native experiments or delete their failures.
2. Emit new `agent_inputs.jsonl` containing ONLY a stable opaque `sample_id` (first 24 hex chars of SHA256 over canonical full packet, with stable domain separator) and the `packet`. No `admissible`, `control`, `source_case`, or control-bearing `id` anywhere on the inference surface.
3. Emit `gold_labels.jsonl` separately, keyed by `sample_id`; preserve original `control`, `source_case`, true label **only inside the separate gold file**. No ambiguous sample-id collisions, no label mismatch or lost cases.
4. Produce `evaluation_manifest.json` with explicit artifact SHA256, base rate, positive/negative counts, original history/provenance. Distinguish labeled training resource from blind input view; do **not** call the public gold artifact a confidential hidden test.
5. Replay deterministically from the previously frozen actual seven-case `authorities.json` plus original `runner.py` with zero copied labels in inference rows. Test a fresh-process second run byte-identical and assert no `original_scoped`, `wrong_ci_run`, `admissible`, etc in sample-id or top-level agent rows.
6. Execute model-free baseline using **equal information**: a separately implemented exact-authority comparison against the same authoritative positive packets. This may tie the typed MathGraph verifier 7/7 true and 0/49 false; **if so, explicitly REJECT uniqueness-of-classifier-advantage**. Compare green-CI-only 49/49 false admissions and always-UNKNOWN 7/7 missed true admissions; report sensitivity and specificity, NOT accuracy only on a 7:49 imbalanced dataset.
7. Freeze this protocol in Git before writing code and before any new evaluated output.

## Remaining epistemic boundaries
This V2 does NOT introduce a hidden independent sample, fresh model-produced patches, tool-using equal-information frontier LLM, causal lifetime cost advantage, new learning method or Kaggle submission. All earlier source-native Fern V2 results remain warranted. The later model-pilot protocol `4aec77a8` remains **UNEXECUTED** pending a trustworthy compute/tool path; do not mislabel its existence as model inference. No model weights or paid inference are needed here.

**Promotion:** WARRANTED_BOUNDED_LEAKAGE_REPAIR_AND_COMPARATOR only if native CI run and independently reopened artifact demonstrate (a) original three leak baselines 56/56, (b) blinded input has none of those signals, (c) all 56 original labels are still correctly scored by source-matched evaluator, (d) equal-information exact comparator tied if expected, (e) reproducibility under process restart. If any gate fails keep UNKNOWN or RED and preserve evidence.
