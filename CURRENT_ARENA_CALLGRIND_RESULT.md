# Current Arena Sokonanoda Callgrind — Result

Run: `34931160101`  
Job: `104259459013`  
Official sokonanoda pin: `28c03d0103e004610e4d47a4828965efb2b70af9`  
Frozen case: `perf/grind-ring-5`  
Artifact: `10380484907`  
Artifact digest: `sha256:c248b4d766d565c457cef603abf780be185c731b3897e80af8df33081cf7f793`

The profiling build used generic x86-64 rather than `target-cpu=native` so
Valgrind could execute it. Checker logic was unchanged. Frozen semantics remained
103 / 103 good accepted and 58 / 58 bad rejected.

Total profiled instructions:

```text
2,644,531,729
```

## Dominant self-instruction costs

- `TypeChecker::eval`: **10.707%**
- `__memset_avx2_unaligned_erms`: **9.123%**
- `prune_env_cold`: **7.797%**
- `eval_no_cache`: **6.514%**
- `neutral_app`: **6.153%**
- `intern_frame`: **5.800%**
- `env_extend`: **5.231%**
- secondary `eval` body: **4.159%**
- `infer_value`: **3.608%**
- rehash of `RawTable<((usize, ExprPtr), Env)>`: **3.303%**
- rehash of `RawTable<((usize, usize), Env)>`: **3.139%**
- `canonicalize_for_spine`: **2.936%**
- `spine_apps`: **1.962%**
- `fire_recursor`: **1.522%**
- rehash of frame `RawTable<Env>`: **1.401%**
- `apply`: **1.182%**

By contrast:

- `spine_snoc_hc`: **0.119%**
- `mk_rigid_hc`: **0.103%**

## Conclusion

The materialized-spine direction is no longer the current Arena frontier.

The present structural hotspot is the **environment representation and its
growth path**:

```text
pruning
+ frame interning
+ environment extension
+ environment-table rehash
+ allocation / clearing
```

The three visible environment-table rehash functions alone account for about:

```text
3.303 + 3.139 + 1.401 = 7.843% self instructions
```

and the large `memset` component is consistent with substantial table/allocation
traffic.

The next diagnostic must measure, without changing semantics, the growth
economics of the exact hot tables—especially:

- `wide_prune`: `(usize, ExprPtr) -> Env`
- `env_hc`: `(usize, usize) -> Env`
- `frames`: exact interned `Env`

before choosing a representation or capacity policy.

No PR is authorized or created by this result.
