# Raw Multichannel Representation Genesis V16 — Frozen Protocol

## Question

Without hand-written physiological markers, summary statistics, spectral features, or learned neural embeddings, can the Minimal Developmental Algorithm construct the smallest raw measurement readout sufficient for verified future consequence?

V16 deliberately separates:

    measurement != representation != consequence

The learner receives only anonymous multichannel measurements through time and intervention-conditioned future outcomes.

It is not told which channels are "markers", which combinations matter, or whether memory is required.

## Primitive measurement interface

For each admitted encounter history h, the learner receives a bounded exact observation window:

    X(h) = [x_t, x_{t-1}, ..., x_{t-L}]

where each x is an anonymous N-channel finite-valued measurement vector.

The only primitive readout generator is:

    ACCESS(lag, channel)

which returns the raw measured value at that location in the supplied window.

No hand-written derived feature is supplied.

Explicitly absent from the frozen core:

- physiological marker names;
- domain labels;
- averages / variances;
- Fourier / frequency features;
- thresholds chosen from the challenge;
- ratios;
- PCA / learned vectors;
- geometry;
- graph features;
- hidden-state identifiers;
- challenge-specific channel combinations.

## Consequence authority

A complete bounded future-intervention table induces the target predictive quotient:

    h ~_F h'
    iff
    every admitted future intervention has the same verified outcome after h and h'.

This target is external authority. It does not reveal hidden state.

A candidate readout set R induces:

    q_R(h) = tuple(ACCESS_r(h) for r in R).

R is sufficient iff q_R induces exactly the same partition as ~_F.

## Initial present

The active readout set is empty:

    R_0 = {}

so all histories are initially represented identically.

## Developmental algorithm

The governing loop is unchanged:

    EXECUTE
    -> VERIFY
    -> DIAGNOSE
    -> CONSTRAIN
    -> RESTRUCTURE
    -> CHOOSE
    -> COMPILE
    -> UPDATE

### EXECUTE
Represent histories using the currently active raw accessors only.

### VERIFY
Compare the induced quotient against the complete future-consequence quotient.

### DIAGNOSE
Find a pair h1,h2 merged by the current readout but distinguished by future consequence.

### CONSTRAIN
Generate all currently authorized ACCESS(lag,channel) readouts that separate the witness.

### RESTRUCTURE
Add the minimum-cost separating readout.

Accessor cost is generic:

    cost(ACCESS(lag,channel)) = 1 + lag

Current measurements therefore cost 1; historical measurements cost more because memory must be retained.

### CHOOSE
Preserve all behaviorally distinct equal-cost minimum repairs.

Independent qualification consequence may eliminate alternatives. Otherwise preserve the frontier.

### COMPILE
After a complete globally minimum readout is independently verified on at least two worlds with the same measurement interface, compile it as an anonymous readout code.

### UPDATE
Use the compiled readout directly on future worlds, but replay-verify it before trust.

## Exact global minimum

For the currently authorized lag depth D, exhaust all generated accessors:

    {(lag,channel) : 0 <= lag <= D, 0 <= channel < N}.

Reduce global readout selection to exact set cover over consequentially distinguishable history pairs.

An accessor covers pair (h,h') iff their raw values differ at that accessor.

A readout is complete iff it covers every pair separated by the full future-consequence quotient.

Minimize lexicographically:

    (# accessors, total accessor cost).

This gives an exact bounded minimum feature-vector proof without hand-designing the feature values.

## Development of memory reach

The initial authorized lag depth is:

    D = 0

Only present measurements are available.

If exhaustive search proves that no lag-0 accessor set can reproduce the future-consequence quotient, this is a certified representational obstruction.

Only then may the learner expand measurement reach:

    D -> D + 1.

Expansion continues minimally until either:
- a complete readout exists; or
- the frozen maximum lag bound is exhausted, yielding typed UNKNOWN/INADEQUACY.

Thus memory is not pre-installed as necessary; it is earned by consequence.

## Required post-freeze gates

### M1 — no hand-engineered features
The frozen core exposes only raw ACCESS(lag,channel), partitioning, exact consequence comparison, bounded search, and compilation.

### M2 — undifferentiated beginning
The initial empty readout has one representation class.

At least one certified future-consequence obstruction must occur before any channel is retained.

### M3 — minimum raw marker bundle emerges
A main hidden world must require at least two raw accessors for complete prediction.

No single accessor may be sufficient.

The globally minimum readout must be proved by exhaustive pair-cover search.

### M4 — distractors disappear
At least half of supplied raw channels in the main world are predictive distractors/redundancies and do not appear in any selected globally minimum code.

### M5 — no premature memory
On the main world, lag-0 suffices.

The learner must not expand to lag-1 merely because historical measurements are available in the raw encounter record.

### M6 — certified memory genesis
A second world must have two histories with identical present raw vectors but different verified futures.

Exhaustive lag-0 search must certify inadequacy.

Only then may lag depth expand to 1, where a complete minimum readout becomes constructible.

### M7 — non-canonicity
A challenge must admit at least two equal-cost minimum raw readout codes.

The learner preserves them until independent future qualification selects one.

### M8 — compiled readout reuse
After the same minimum readout is independently verified on two hidden-state renamings with the same raw measurement interface:
- compile an anonymous readout code;
- warm third-world replay succeeds with zero acquisition search;
- cold zero-acquisition returns UNKNOWN_READOUT;
- ablation restores UNKNOWN_READOUT.

### M9 — wrong dynamics falsify retained readout
A same-interface world with changed hidden dynamics must replay-check and reject the retained readout if it no longer reproduces the future-consequence quotient.

Development/search then resumes.

### M10 — heterogeneous world
The same frozen learner must construct a different minimum readout in a structurally different hidden system.

### M11 — incomplete authority
An incomplete future-consequence table returns UNKNOWN_AUTHORITY.

### M12 — accessor ablation
If raw ACCESS construction is disabled, no feature/marker growth is authorized.

### M13 — no vector ontology requirement
The scientific output is a consequence-sufficient set of raw accessors plus the induced quotient.

The kernel does not assume that a vector is the final ontology. It reports the quotient as primary and the minimum readout as one implementation of it.

## Interpretation

A successful readout such as:

    {(0,2), (0,5)}

may be interpreted after the fact as a two-marker panel.

A successful readout such as:

    {(0,3), (1,1)}

may be interpreted as a present measurement plus a memory-dependent marker.

But those names are external glosses. The learner only retains raw distinctions that change verified future consequence.

## Claim boundary

A pass establishes only:

> in bounded exact multichannel dynamical worlds, a minimum predictive raw-measurement readout can be constructed from anonymous measurements without hand-engineered features, and memory depth can be expanded only when present measurements are proved insufficient.

It does not establish:
- clinical biomarkers;
- noisy/statistical validity;
- continuous physiology;
- causal sufficiency of observational measurements without interventions;
- natural-world grounding;
- optimal sensor design;
- that raw coordinate subsets are the final representation language.

The next boundary after a pass is stochastic/noisy multichannel data, where exact equality must be replaced by statistically warranted predictive equivalence and rate-distortion-style compression.
