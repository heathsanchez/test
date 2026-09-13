# Stochastic Memory Genesis V19 — Frozen Protocol

## Question

Can temporal memory itself be earned from noisy multichannel consequence, without hand-written physiological markers, temporal features, windows, frequencies, trends, or a manually chosen evidence threshold?

V16 showed exact memory reach can expand only after present measurements are certified insufficient.
V18 repaired the stochastic readout criterion using:
- Jeffreys/Krichevsky-Trofimov predictive evidence;
- one structural bit per retained present ACCESS token.

V19 combines them.

## Primitive measurement language

The learner receives exact anonymous raw measurement windows:

    x_t, x_{t-1}, ..., x_{t-Dmax}

and repeated binary future-intervention outcome counts.

The only generated measurement primitive is:

    ACCESS(lag, channel)

No derived feature is supplied.

Explicitly absent:
- physiological marker names;
- moving averages;
- slopes;
- derivatives;
- frequency/spectral features;
- thresholds;
- ratios;
- PCA;
- neural embeddings;
- hidden-state identifiers.

## Statistical consequence code

For a candidate readout R:
1. partition contexts by exact raw values under R;
2. pool outcome counts inside each predictive cell;
3. use the Jeffreys/Krichevsky-Trofimov Beta(1/2,1/2) marginal code for every cell/intervention;
4. add structural code

       L_struct(R) = sum_{(lag,c) in R} (1 + lag).

No fitted coefficient is used.

A present measurement costs 1.
A one-step memory access costs 2.
Deeper memory costs proportionally more.

This is not a domain preference for recent physiology; it is the generic cost of retaining more temporal machinery.

## Developmental reach

Initial authorized memory depth:

    D = 0.

At depth D, exhaust every subset of:

    {(lag,c) : 0 <= lag <= D}.

Let B_D be the globally minimum total code length at that depth.

To consider expansion from D to D+1, compute the globally minimum candidate code in the one-step-enlarged language.

Memory expansion is authorized iff:

    B_{D+1} < B_D

strictly.

If not, the smaller reach is retained.

Thus historical measurements are available to the external encounter record but do not enter the learner's active language unless future consequence pays their structural cost.

## Minimal Developmental Algorithm

    EXECUTE -> VERIFY -> DIAGNOSE -> CONSTRAIN
    -> RESTRUCTURE -> CHOOSE -> COMPILE -> UPDATE

EXECUTE:
    use the current minimum readout.

VERIFY:
    compare universal predictive code length.

DIAGNOSE:
    determine whether extending memory reach yields a strictly better warranted code.

CONSTRAIN:
    allow only the next lag depth.

RESTRUCTURE:
    exhaustively search the minimally enlarged raw-accessor language.

CHOOSE:
    preserve exact equal-score minima; qualification data may select.

COMPILE:
    after independent recovery, compile the anonymous readout.

UPDATE:
    future worlds replay-verify it before trust.

## Required post-freeze gates

T1. Frozen core uses only ACCESS(lag,channel), KT count evidence, and structural lag cost.
T2. A present-sufficient noisy world selects a minimal present-only readout and never authorizes lag-1.
T3. A memory-required world retains the empty/present model at lag-0, then strictly improves at lag-1 and selects a historical raw accessor.
T4. A mixed world selects one present accessor plus one historical accessor; neither alone is globally optimal.
T5. Independent noise realization recovers the same memory-dependent readout.
T6. Low-data world does not authorize memory expansion.
T7. Distractor present/historical channels are excluded.
T8. Two independent recoveries compile the temporal readout; warm replay is zero-acquisition; cold and ablation controls remain UNKNOWN.
T9. Same-interface changed temporal dynamics falsify replay and trigger redevelopment.
T10. Incomplete count authority remains UNKNOWN.
T11. Removing statistical consequence scoring authorizes no memory growth.
T12. Removing historical ACCESS from the candidate language prevents the memory-required world from silently inventing a temporal summary.

## Claim boundary

A pass establishes only:

> in bounded synthetic noisy multichannel worlds, temporal memory depth and a minimum raw temporal readout can be consequence-earned under a generic universal predictive code, without hand-engineered temporal features.

It does not establish clinical biomarkers, continuous physiology, natural-world causal sufficiency, optimal sampling rate, or that raw lag accessors are the final representation language.
