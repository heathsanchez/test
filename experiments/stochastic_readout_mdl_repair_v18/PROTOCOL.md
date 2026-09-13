# Stochastic Readout MDL Repair V18 — Frozen Protocol

## Why V18 exists

V17 was a genuine scientific failure:

`STOCHASTIC_PREDICTIVE_READOUT_V17_GAPS_EXPOSED`

Its Jeffreys/Krichevsky-Trofimov data code behaved as intended, but its subset-description term

    log2(M+1) + log2(binomial(M,k))

was not monotone in retained-accessor count. For M=6 it assigned less structural cost to k=6 than to k=2, so redundant constant accessors could be rewarded rather than penalized.

V18 does not alter the data evidence model or the no-hand-tuning measurement language. It repairs only the structural description language.

## Frozen scientific constitution

Measurements:
    anonymous raw current-channel ACCESS(channel) only.

Stochastic consequence evidence:
    binary outcome counts per context and future intervention.

Predictive data code:
    exact Jeffreys/Krichevsky-Trofimov Beta(1/2,1/2) marginal code per predictive cell/test.

Structural code:
    one bit of structural cost per retained ACCESS token:

        L_struct(R) = |R|.

This directly inherits the V16 structural language in which each retained raw accessor is one unit of present machinery.

There is:
- no domain marker weight;
- no tuned sparsity coefficient;
- no challenge-specific threshold;
- no frequency/statistical feature engineering.

Total score:

    L(R) = L_KT(data | partition induced by R) + |R|.

The globally selected representation is the raw accessor subset minimizing L(R) over every subset.

## Why this repair is principled

The statistical code answers:
    how costly are the observed future consequences under this predictive partition?

The structural code answers:
    how much present machinery is retained?

These are exactly the two terms already separated by the Minimal Developmental Algorithm:

    consequence adequacy + present complexity.

A redundant accessor that changes no predictive partition cannot improve the KT term and necessarily increases structural cost by 1.

No coefficient is fitted.

## Developmental law

Start from the empty readout.

Growth is authorized only when a non-empty readout has strictly lower total code length than the empty present.

Retain globally minimum readouts.
Preserve exact equal-cost non-canonicity.
Use independent future data to select if supplied.
Compile only after independent recurrence.
Replay before trust.
Return UNKNOWN at authority boundaries.

The developmental loop remains:

    EXECUTE -> VERIFY -> DIAGNOSE -> CONSTRAIN
    -> RESTRUCTURE -> CHOOSE -> COMPILE -> UPDATE

## Post-freeze gates

Use the same frozen challenge family as V17 so the repair is tested prospectively against the previously exposed residual.

R1. Main noisy world selects exactly the two causally useful raw accessors.
R2. A second independent noise realization selects the same readout.
R3. Independent qualification realization selects the same global optimum.
R4. Redundant/distractor channels are excluded.
R5. Equal-cost noncanonical raw readouts remain tied until independent qualification.
R6. Two independent recoveries compile the readout; warm replay uses zero global acquisition search; cold and ablation controls fail conservatively.
R7. Same-interface changed dynamics falsify the retained readout and redevelop to a different minimum.
R8. Low-data realization retains the empty present provisionally.
R9. Heterogeneous noisy world learns a different minimum readout.
R10. Incomplete authority remains UNKNOWN.
R11. Removing statistical consequence scoring authorizes no growth.
R12. Adding a raw accessor that induces no partition change must strictly worsen structural score by exactly one bit while leaving the KT data term unchanged.

## Claim boundary

A pass establishes only that, in bounded synthetic noisy multichannel worlds, the V16 no-hand-tuning result survives sampling noise under a generic KT predictive evidence code plus the already-established one-token-per-accessor structural cost.

It does not establish clinical biomarkers, continuous physiology, passive causal identification, natural-world validity, or optimal sensor design.
