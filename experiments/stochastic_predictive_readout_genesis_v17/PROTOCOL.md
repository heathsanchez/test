# Stochastic Predictive Readout Genesis V17 — Frozen Protocol

## Question

Can V16's no-hand-tuning result survive sampling noise without introducing hand-engineered physiological features or a manually chosen predictive-loss threshold?

V17 keeps the raw measurement language unchanged:

    ACCESS(channel)

and replaces exact future outcomes with repeated stochastic outcome counts.

The learner receives only:
- anonymous raw multichannel contexts;
- anonymous future intervention tests;
- observed outcome counts for each context/test;
- a complete finite measurement interface.

No domain marker names, thresholds, Fourier features, averages, ratios, PCA, or neural embeddings are supplied.

## Statistical constitution

Model comparison uses an order-invariant universal Bayesian/MDL code:

- binary future outcomes;
- independent Jeffreys/Krichevsky-Trofimov prior Beta(1/2,1/2) per predictive cell and intervention test;
- exact Dirichlet-multinomial marginal likelihood;
- model-description cost for choosing k accessors from M:

    L_model = log2(M+1) + log2(binomial(M,k)).

For a candidate accessor subset R:

1. partition contexts by their raw values under R;
2. pool outcome counts inside each resulting cell;
3. compute negative log2 marginal evidence for every cell/test;
4. add L_model.

The selected representation is the globally minimum total description length over every raw accessor subset.

There is no tunable loss weight and no challenge-specific threshold.

## Developmental rule

Start with the empty readout.

Growth is authorized only when some non-empty raw readout has strictly shorter total universal codelength than the empty readout.

If the empty readout remains optimal, retain it provisionally; do not assert that the world is truly homogeneous.

The Minimal Developmental Algorithm remains:

    EXECUTE -> VERIFY -> DIAGNOSE -> CONSTRAIN
    -> RESTRUCTURE -> CHOOSE -> COMPILE -> UPDATE

## Replay

A compiled readout is replay-qualified without global rediscovery if:
- its universal codelength beats the empty readout; and
- deleting any one retained accessor makes the code no better.

This is a local verification of the retained mechanism, not a claim of renewed global optimality.

If replay fails, development resumes with exhaustive global search.

## Required post-freeze gates

N1. Frozen core contains only raw accessor subsets and universal count coding.
N2. Main noisy world selects a two-accessor readout; no single accessor wins.
N3. Same readout is independently recovered from a second noise realization.
N4. At least half of raw channels are excluded.
N5. Independent qualification noise retains the same optimum.
N6. A non-canonical training world produces tied equal-cost raw readouts; independent qualification selects one.
N7. Two independent recoveries compile the readout; warm replay uses zero global acquisition search; cold zero-search is UNKNOWN; ablation restores UNKNOWN.
N8. Same-interface changed dynamics falsify replay and trigger redevelopment to a different readout.
N9. With very little data, the empty readout remains provisionally optimal and no marker is compiled.
N10. Same frozen learner finds a different optimum in a heterogeneous stochastic world.
N11. Incomplete count authority returns UNKNOWN_AUTHORITY.
N12. Removing statistical consequence scoring authorizes no growth.

## Claim boundary

A pass establishes only that, in bounded synthetic stochastic multichannel worlds, raw predictive readouts can be selected under sampling noise by a generic universal-code criterion without domain feature engineering.

It does not establish clinical biomarkers, continuous physiology, causal identification from passive observation, optimal experimental design, or natural-world validity.
