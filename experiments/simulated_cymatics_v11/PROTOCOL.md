# Simulated Cymatics V11 — Frozen Protocol

## Question

Can the same relation/composition/reification programme recover a useful standing-pattern language from exact anonymous vibration data without supplying coordinates, frequency, phase, node, mode, wavelength, eigenvector, or geometry labels?

V8 reduced the finite semantic object basis to relation + composition with verified reification.
V9 asks whether finite recurrence and future-trace classes arise without a frequency primitive.
V10 showed coordinate-free causal spatial structure can be reconstructed from anonymous intervention consequences.

V11 combines those two axes in a finite exact vibration surrogate.

## What the frozen kernel is allowed to see

For each world:

1. N anonymous channels.
2. Binary one-step intervention consequences:
       source channel i -> which channels change next.
3. A finite sequence of anonymous channel-value frames:
       u_0, u_1, ..., u_T
   where each frame is an N-tuple over a finite value alphabet.
4. A distinguished rest/baseline value supplied as part of the measurement interface.
5. Search/completeness bounds.

The kernel is **not** given:

- channel coordinates;
- dimension or geometry;
- adjacency labels;
- drive frequency;
- temporal phase;
- period/cycle/frequency primitives;
- node/nodal-line labels;
- mode/eigenmode labels;
- wavelength;
- graph-family labels;
- the update equation.

## Frozen operations

### Spatial construction
Infer each one-step influence row exactly from intervention observations.
Use relational COMPOSE to construct complete bounded multi-step reachability.
Reify mutual-reach components and generic degree/distance invariants.

### Temporal construction
Treat the observed dynamics as ordered frame relations.
Search for the least positive displacement k for which the consecutive-frame state pair

    (u_t, u_{t+1})

returns to its initial pair and the available trace replays consistently over the declared verification window.

This is equality/recurrence search, not spectral analysis.

### Persistent consequential invariance
Once a verified return length k exists, inspect exactly one verified return block.
A channel belongs to the persistent-baseline set iff its observed value equals the supplied baseline at every frame in that block.

No special semantic status is attached to such channels by the kernel.

### Relational organization of invariant sets
Restrict the recovered influence relation to:
- persistent-baseline channels;
- all other channels.

Construct their relational connected components by repeated COMPOSE/reachability.

The resulting structural record may contain only generic quantities such as:
- return length;
- persistent-set size;
- component-size multisets;
- incidence counts between persistent and non-persistent sets;
- anonymous relation signatures.

### Compilation
If the same complete pattern signature is independently verified in two relabelled worlds, it may be compiled as an anonymous pattern atom and directly replayed on a third relabelled world.

No human pattern name is attached.

## Post-freeze challenge families

### C1 — hidden finite membrane surrogate
An exact finite second-order wave-like dynamics is generated on a hidden 3x3 interaction graph over a finite value alphabet. Channel labels are permuted. The trajectory contains a non-empty persistent-baseline subset that forms one connected separator-like relational structure.

The kernel must recover:
- exact one-step influence relation;
- least verified frame-pair return;
- persistent-baseline set;
- its relational organization.

### C2 — permutation transfer
Two differently relabelled copies of the same dynamical world must produce the same canonical pattern signature.

### C3 — causal pattern compilation
After two verified relabelled copies, a third copy must be replayable against the compiled anonymous pattern atom with zero pattern-search acquisition.
A cold zero-acquisition kernel must return UNKNOWN_PATTERN.
Ablation of the atom must restore that behavior.

### C4 — same spatial carrier, different pattern
A different initial condition on the same hidden interaction graph produces a different persistent-baseline organization. A retained pattern atom must fail replay and the kernel must reconstruct the new signature rather than trusting the old one.

### C5 — unseen geometry
A hidden nine-channel path-like interaction world with exact second-order dynamics must be analyzed by the same frozen kernel. It has a different verified return length and a different persistent-baseline organization.

### C6 — incomplete temporal horizon
A trace ending before the first verified frame-pair return must yield UNKNOWN_TEMPORAL_REPLAY.

### C7 — incomplete spatial observation
With one intervention source withheld, return UNKNOWN_INFLUENCE; do not infer missing geometry from the vibration trace.

### C8 — COMPOSE ablation
Without COMPOSE, direct local intervention rows remain reconstructible, but multi-step relational organization of the invariant subset must remain unresolved.

### C9 — temporal-replay ablation
Without temporal replay search, spatial structure remains available but the persistent-baseline pattern must not be certified from an arbitrary prefix.

## Exact challenge physics

The challenge generator may use coordinates, graph families, and a second-order update law internally to create worlds **after the scientific freeze**. Those generator-side concepts are hidden from the kernel and are not part of its language.

All arithmetic is finite and exact so there is no threshold tuning, FFT, floating-point tolerance, or visual classifier.

## Claim boundary

A pass establishes only:

> in an exact finite vibration surrogate, recurrence-like temporal structure plus coordinate-free causal relations are sufficient to construct and transfer a persistent standing-pattern representation without supplied frequency, phase, nodal, modal, or coordinate primitives.

It does not establish physical cymatics, continuous wave mechanics, spectral decomposition, real sensor robustness, natural-world grounding, or that persistent-baseline sets are the uniquely best physical representation.

The next boundary after a pass is a less curated simulation in which useful spatial/temporal abstractions must be chosen by prospective prediction rather than being directly evaluated as named pattern gates; after that, real cymatics data.
