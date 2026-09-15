# A6 Materialized-Key Raw Spine Interner — Result

## Verdict

```text
MATERIALIZED_SPINE_PROCEED_MATHLIB
```

Run: `34927284163`  
Job: `104247892307`  
Head: `a6fce15302d779f8969fce3b3daa609fe0b8cb7a`  
Artifact: `10380069979`  
Artifact digest: `sha256:54ac3222638906180ebe1d201168767e4a8754880dc51296b920f27ccb458d96`

## Candidate

Replace the authoritative spine interner with:

```text
HashTable<(prev_pointer, elim_key, S)>
```

The exact identity is materialized when the spine is interned rather than
reconstructed by dereferencing `S` during future probes.

No secondary cache.
No threshold.
No workload classifier.
No changed equality relation.

## Frozen semantics

All three arms passed the external oracle exactly:

- A0: 103 / 103 good accepted; 58 / 58 bad rejected
- S-only raw: 103 / 103 good; 58 / 58 bad
- materialized-key raw: 103 / 103 good; 58 / 58 bad

## Development

30 paired randomized-order repetitions on the frozen four-case workload.

Materialized-key raw vs A0:

- median paired CPU delta: **-10.1005%**
- wins: **30 / 30**

Materialized-key raw vs S-only raw:

- median paired CPU delta: **-1.7472%**
- wins: **24 / 30**

S-only raw vs A0:

- median paired CPU delta: **-8.5451%**
- wins: **29 / 30**

Development verdict:

```text
MATERIALIZED_SPINE_PROCEED_HELDOUT
```

## Disjoint held-out

Same frozen 24-case held-out workload.

Materialized-key raw vs A0:

- median paired CPU delta: **-1.0432%**
- wins: **20 / 30**

Materialized-key raw vs S-only raw:

- median paired CPU delta: **-1.4735%**
- wins: **23 / 30**

S-only raw vs A0:

- median paired CPU delta: **+1.2196%**
- wins: **10 / 30**

Held-out verdict:

```text
MATERIALIZED_SPINE_PROCEED_MATHLIB
```

## Scientific interpretation

The prior transfer failure was not caused by prehashed authoritative interning
itself.

It was caused materially by reconstructing an already-earned exact identity
from the stored semantic object on every successful probe.

The winning representation stores:

```text
identity + consequence
```

together.

This supports the general law:

```text
once a consequential identity has been earned at construction time,
materialize it where future exact reuse needs it instead of repeatedly
reconstructing it from the object it names.
```

The next and only authorized escalation is the already-frozen full Mathlib
benchmark. No candidate parameter may change before that test.
