# A6 Prehashed Authoritative Spine Interner — Result

## Verdict

```text
PREHASHED_SPINE_STOP_HELDOUT
```

Run: `34925768301`  
Job: `104243385191`  
Head: `f9b0ca9a540a7c52d8ff44880d717fcedefc23ec`  
Artifact: `10380281089`  
Artifact digest: `sha256:48026d82247423feb79ce00657358bb3ceb92819fdf9ea3e392df753a72ad677`

## Semantics

All three frozen arms passed the external oracle:

- A0: 103 / 103 good, 58 / 58 bad
- prehashed authoritative table: 103 / 103 good, 58 / 58 bad
- prehash-cost control: 103 / 103 good, 58 / 58 bad

## Development

30 paired repetitions over the frozen four-case development workload.

Prehashed vs A0:

- median paired CPU delta: **-8.3154%**
- wins: **28 / 30**

Prehashed vs prehash-cost control:

- median paired CPU delta: **-9.3341%**
- wins: **30 / 30**

Prehash-cost control vs A0:

- median paired CPU delta: **+1.1174%**
- wins: **12 / 30**

Per-case prehashed vs A0:

- `perf/grind-ring-5`: **-9.9127%**, 29 / 30 wins
- `init-prelude`: **-2.4861%**, 22 / 30 wins
- `perf/app-lam`: **+0.2766%**, 14 / 30 wins
- `perf/shift-cascade`: **+0.2173%**, 14 / 30 wins

Development verdict:

```text
PREHASHED_SPINE_PROCEED_HELDOUT
```

## Disjoint held-out

The 24-case held-out workload was frozen before candidate performance.

Prehashed vs A0:

- median paired CPU delta: **+1.2609%**
- wins: **10 / 30**

Prehashed vs prehash-cost control:

- median paired CPU delta: **+1.5591%**
- wins: **7 / 30**

Held-out verdict:

```text
PREHASHED_SPINE_STOP_HELDOUT
```

## Interpretation

This is a strong structural separator.

Replacing the authoritative spine `FxHashMap` with an exact prehashed
`HashTable<S>` is a large, repeatable win on the heavy spine workload and a
smaller win on `init-prelude`, but it is not a universal representation win.

The neutral development cases and the disjoint small held-out corpus show that
the raw-table representation has a fixed/small-regime cost.

Therefore the next question is not whether prehashed spine interning works. It
does.

The next question is:

```text
when has the spine interner become large/hot enough that the raw
representation has earned its activation cost?
```

The next diagnostic measures baseline spine-interner scale without changing
semantics. A hybrid representation will be allowed only if a scale boundary is
frozen before hybrid performance is observed.
