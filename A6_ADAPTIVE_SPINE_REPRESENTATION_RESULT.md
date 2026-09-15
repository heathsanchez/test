# A6 Adaptive Spine Representation — Result

## Verdict

```text
ADAPTIVE_SPINE_STOP_HELDOUT
```

Run: `34926644776`  
Job: `104246001231`  
Head: `0079d518db46ce7bcfbac6a2881247eb408acd2b`  
Artifact: `10380361203`  
Artifact digest: `sha256:98ceef1cc1f4f1490c8795c62d4d6e59fd01876821a660e78be6234c18a81837`

## Candidate

Each session starts with the original A0 `FxHashMap` and migrates exactly to
the prehashed raw spine table at the preregistered peak-size separator:

```text
THRESHOLD = 65
```

The threshold was fixed by run `34926408611` before hybrid performance.

## Semantics

All three arms were exact:

- A0: 103 / 103 good, 58 / 58 bad
- threshold-65 hybrid: 103 / 103 good, 58 / 58 bad
- always-raw control: 103 / 103 good, 58 / 58 bad

## Development

Hybrid vs A0:

- median paired CPU delta: **-5.4034%**
- wins: **30 / 30**

Always-raw vs A0:

- median paired CPU delta: **-7.0060%**
- wins: **30 / 30**

Hybrid vs always-raw:

- median paired CPU delta: **+1.7295%**
- wins: **0 / 30**

Development verdict:

```text
ADAPTIVE_SPINE_PROCEED_HELDOUT
```

## Disjoint held-out

Hybrid vs A0:

- median paired CPU delta: **-0.7836%**
- wins: **17 / 30**

Always-raw vs A0:

- median paired CPU delta: **+1.1567%**
- wins: **9 / 30**

Hybrid vs always-raw:

- median paired CPU delta: **-1.1987%**
- wins: **21 / 30**

The frozen held-out admission rule required at least 18 / 30 wins.

Therefore the hybrid is **not admitted**, despite the negative median delta.

## Interpretation

The adaptive representation materially improved transfer:

```text
always raw:  +1.1567% vs A0 on held-out
adaptive 65: -0.7836% vs A0 on held-out
```

but the win count remained unresolved at 17 / 30.

The threshold is not retuned.

A deeper representation residual remains: the S-only raw table reconstructs
each stored exact key by dereferencing the stored spine object during lookup.
That pointer chase is avoidable because the exact key is already known at
insertion.

The next candidate materializes the exact key inline in the raw table entry,
preserving the same equivalence and lookup hash while eliminating key
reconstruction from stored semantic objects.
