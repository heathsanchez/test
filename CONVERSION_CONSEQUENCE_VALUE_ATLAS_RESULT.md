# Conversion Consequence Value Atlas — Result

Run: `34920132248`  
Job: `104226187873`  
Commit: `a2bfd9f122c38e534ccc70a2da264fee1726c0a9`  
Artifact: `10377807381`  
Artifact digest: `sha256:fb72a11e1a85b9b94e246f79a6ec1dccb180ea65e00203c49f2401f847f6bc7e`

The atlas was diagnostic-only. Existing conversion caches remained authoritative.

Shadow identity included:

- already-earned representative pair;
- rigid/non-rigid mode;
- depth;
- probe depth;
- remaining probe budget.

The first actual boolean result for a shadow signature was retained only for
consistency checking. Repeated signatures were recomputed normally.

## Frozen corpus result

Across **181,998** real conversion-cache misses:

- dependency-complete shadow repeats: **23**
- recursive unify calls spent on repeats: **38**
- mean recursive unify calls per repeat: **1.65**
- maximum recursive unify calls for one repeat: **5**
- measured repeat time: **6,423 ns** total
- maximum repeat time: **952 ns**
- repeated true outcomes: **23**
- repeated false outcomes: **0**
- contradictions: **0**

Cost distribution:

- 1 unify call: 12
- 2–4 calls: 10
- 5–16 calls: 1
- 17+ calls: 0

## Conclusion

Conversion is not a valuable consequence-reuse frontier under the frozen corpus.

The current conversion machinery already captures nearly all economically
meaningful recurrence. The remaining dependency-complete repeats are too rare
and too cheap to justify another cache layer.

This branch is closed. Priority remains the type-inference consequence-value
atlas, where one miss can recursively invoke inference, evaluation, sort checks,
and definitional equality.
