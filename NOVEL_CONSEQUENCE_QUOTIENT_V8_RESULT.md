# V8 Development Gate — Result

## Verdict

```text
V8_STOP_BEFORE_MATHLIB
```

Run: `34920530472`  
Job: `104227428340`  
Commit: `36e5642cf4a4f4f05e3a89504199b5335ae9f24e`  
Artifact: `10377673761`  
Artifact digest: `sha256:3f83f99b935563a2cfc1e318b8f595a5342ffaa3046cdf667b56ba2e2b630f16`

## Semantic gate

All three arms remained exact on the frozen external oracle:

- A0: 103 / 103 good accepted, 58 / 58 bad rejected
- V8 candidate: 103 / 103 good accepted, 58 / 58 bad rejected
- matched recompute ablation: 103 / 103 good accepted, 58 / 58 bad rejected

## Development economics

Arena-style PGO builds were used for all arms.

### grind-ring-5

Candidate versus matched ablation:

- median paired CPU delta: **+1.5167%**
- candidate wins: **4 / 30**

Candidate versus A0:

- median paired CPU delta: **+0.0919%**
- candidate wins: **15 / 30**

### init-prelude

Candidate versus matched ablation:

- median paired CPU delta: **+3.9668%**
- candidate wins: **4 / 30**

Candidate versus A0:

- median paired CPU delta: **+1.3152%**
- candidate wins: **12 / 30**

## Conclusion

The dependency-complete type-consequence reuse mechanism is semantically clean
but economically wrong.

The exact environment/context comparison and seed machinery cost more than the
repeated inference work they avoid, even on the two workloads where the shadow
atlas found essentially all of the recurrence.

Mathlib was therefore not run.

This is a decisive residual:

```text
do not compute a new equivalence relation merely to save a small consequence.
```

The next search is restricted to consequences whose semantic identity has
already been earned by the checker for another purpose, so reuse can be tested
with near-zero incremental identity cost.
