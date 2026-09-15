# A6 Earned-Only Apply — Result

## Verdict

```text
EARNED_ONLY_STOP_DEVELOPMENT
```

Run: `34922765079`  
Job: `104234293678`  
Commit: `c7127b078215cb18a06cb73bb5525e1677188564`  
Artifact: `10378568455`  
Artifact digest: `sha256:889f08d2dd06ca36b294ed9c07bed149d640f30fdb126d3a59eda6bcf2862033`

## Frozen semantic oracle

All three arms were exact:

- A0: 103 / 103 good accepted, 58 / 58 bad rejected
- earned-only: 103 / 103 good accepted, 58 / 58 bad rejected
- raw ablation: 103 / 103 good accepted, 58 / 58 bad rejected

So eager canonical/hash-consed construction is not required for correctness on
the frozen corpus. Its value is performance.

## Development economics

Arena-style PGO builds were used for every arm.

Combined four-case development workload:

- A0 median CPU: **0.829719 s**
- earned-only median CPU: **0.838862 s**
- raw median CPU: **0.8573765 s**

Earned-only versus A0:

- median paired CPU delta: **+0.7404%**
- wins: **3 / 30**

Earned-only versus raw:

- median paired CPU delta: **−2.0748%**
- wins: **27 / 30**

Per-case earned-only versus A0:

- `init-prelude`: **−0.1097%**, 16 / 30 wins
- `app-lam`: **+8.1593%**, 1 / 30 wins
- `grind-ring-5`: **+0.3007%**, 10 / 30 wins
- `shift-cascade`: **+0.9255%**, 12 / 30 wins

The disjoint held-out workload and Mathlib were not run because the frozen
development gate failed.

## Conclusion

The current canonicalization/hash-consing path is expensive but causally
valuable.

The raw ablation is materially worse, and even preserving the canonical path
only after identity has already been earned loses to eager A0.

Therefore the next intervention must **preserve the reuse semantics while
lowering the cost of successful lookup/interning**.

The priority target is the three profiled hot tables:

```text
spine_snoc_hc
mk_rigid_hc
mk_unfold_hc
```

The next diagnostic measures exact short-range key locality so that a tiny,
exact front cache can be justified before changing production behavior.
