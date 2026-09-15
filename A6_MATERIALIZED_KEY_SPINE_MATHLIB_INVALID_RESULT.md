# A6 Materialized-Key Spine Mathlib Attempt — Invalid Baseline

Run: `34929042241`  
Job: `104253197050`  
Artifact: `10381294073`

## Status

```text
INVALID_FOR_CANDIDATE_INFERENCE
```

The full Mathlib export and all three PGO builds completed successfully.

The correctness/timing phase then failed on the **first warmup arm**, A0/A6,
before either the S-only raw or materialized-key candidate was run.

A0 panic:

```text
src/inductive.rs:970:9
assertion failed:
self.is_valid_ind_app_v(st, parent_ind_name, depth, cur)
```

All four checker threads panicked and the main thread failed while joining them.

Therefore:

- this run does **not** show a materialized-key Mathlib failure;
- this run does **not** provide a Mathlib performance comparison;
- no candidate arm reached the frozen Mathlib timing gate;
- the baseline/Mathlib pairing itself was invalid for this experiment.

The follow-up uses the current official Arena sokonanoda pin directly rather
than the retained A6 lineage.
