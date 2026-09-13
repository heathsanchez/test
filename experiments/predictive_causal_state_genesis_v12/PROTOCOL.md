# Predictive Causal-State Genesis V12 — Frozen Protocol

## Question

Starting from no domain ontology and an initially undifferentiated representation, can the developmental algorithm construct the minimum consequence-sufficient state language from raw intervention/observation histories alone?

This experiment deliberately does **not** ask the system to find:
- objects;
- space;
- coordinates;
- adjacency;
- frequency;
- phase;
- nodes;
- modes;
- fields;
- numbers-as-features;
- hand-written pattern classes.

The scientific target is closer to deterministic computational mechanics / predictive-state reconstruction:

    two histories are the same state iff every admitted future intervention test produces the same future observation consequence.

The developmental target is the Minimal Developmental Algorithm:

    EXECUTE -> VERIFY -> DIAGNOSE -> CONSTRAIN
    -> RESTRUCTURE -> CHOOSE -> COMPILE -> UPDATE

with the standing law:

    maintain the smallest present sufficient for verified consequence;
    grow only when consequence certifies inadequacy;
    preserve incomparable minimal repairs;
    let independently verified future consequence select among them;
    compile what transfers;
    return UNKNOWN at the warrant boundary.

## What is primitive to the learner

Only:

1. a finite anonymous action alphabet A;
2. a finite anonymous observation alphabet O;
3. ordered encounter histories of action/observation pairs;
4. a finite set of future intervention tests, each itself only an action string;
5. an external consequence table saying what future observation string actually follows when a test is applied after a history;
6. a finite completeness bound over the declared histories/tests.

No hidden state identifiers are visible to the kernel.

The challenge generator may contain hidden states and dynamics **after the scientific freeze**, but those are never passed to the kernel.

## Initial present

The learner begins with:

    active_tests = {}

Therefore every encountered history is represented identically:

    q_0(h) = *

This is the experimentally meaningful version of "starting from nothing":

    no domain ontology and no distinctions beyond raw encounter succession.

It is not metaphysical nothing.  The experiment still supplies encounters, interventions, observations, order, finite bounds, and external authority.

## Consequential identity

For a declared complete test set T:

    h ~_T h'
    iff
    for every t in T,
    consequence(h,t) = consequence(h',t).

The full bounded predictive quotient is therefore not hand-labelled.  It is induced entirely by future intervention consequences.

A current representation based on active test set S subseteq T is:

    q_S(h) = tuple(consequence(h,t) for t in S).

If q_S identifies two histories that the complete future consequence relation distinguishes, the current present is certified too coarse.

## Developmental transition

### EXECUTE
Use the current active-test representation q_S.

### VERIFY
Compare q_S against the complete bounded future-consequence equivalence.

### DIAGNOSE
Produce a witness pair h1,h2 such that:

    q_S(h1) = q_S(h2)

but

    h1 not~_T h2.

This is a certified representational obstruction.

### CONSTRAIN
Enumerate every not-yet-active future test that separates the witness pair.

Candidate repairs are one-test extensions:

    S' = S union {t}.

### RESTRUCTURE
Construct all minimal-cost separating extensions.

Test cost is structural only:

    cost(t) = length(t).

No semantic feature weights exist.

### CHOOSE
Preserve all behaviorally distinct minimal repairs.

If an independently frozen qualification table is supplied, eliminate only candidates whose induced quotient fails that future consequence.

If multiple incomparable candidates remain, return a frontier rather than selecting syntactically.

### COMPILE
When a complete minimum active-test set has been independently qualified, compile that set as an anonymous predictive code.

### UPDATE
The compiled code becomes the new present for future execution/reuse.

## Global minimum requirement

The kernel must also exhaustively verify that the final predictive code is minimum within the declared finite candidate universe.

Search all active-test subsets by increasing structural cost:

    (number of tests, total action-string length)

using Pareto minimality.

No larger code may be declared canonical if a smaller complete code exists.

If several incomparable minimum codes exist and qualification does not distinguish them, preserve all.

## Post-freeze challenges

### G1 — blank-to-disturbance genesis
A hidden deterministic world begins in a homogeneous baseline.  One anonymous intervention introduces a nontrivial latent disturbance.  The learner starts with one representational state and must split only when future consequences force it.

Required evidence:
- initial representation has one class;
- at least one certified obstruction occurs;
- no domain feature names are used;
- the final predictive quotient has multiple states;
- every final split is witnessed by a future intervention consequence.

### G2 — minimum predictive quotient
On a complete bounded encounter set, the final learned quotient must exactly equal the full future-consequence quotient.

The final active-test code must be inclusion/cost minimal within the declared candidate universe.

### G3 — no premature ontology
Before a distinguishing future test is admitted, histories with identical current consequence signatures must remain identified.

The kernel may not split by hidden-state ID, raw history length, action count, channel name, or challenge metadata.

### G4 — non-canonicity
A challenge must admit at least two incomparable equal-cost minimal repairs at an intermediate obstruction.

The kernel must preserve the repair frontier.

An independently frozen qualification family then selects one branch by future consequence.

### G5 — compilation and causal reuse
After the same minimum predictive code is independently verified on two worlds with the same anonymous action/observation interface but different hidden-state naming, compile the code.

On a third renamed world:
- warm code must solve with zero acquisition search;
- cold zero-acquisition must return UNKNOWN_CODE;
- ablation of the compiled code must restore UNKNOWN_CODE.

Every retained code is replay-verified before trust.

### G6 — wrong retained code
A same-interface world with different hidden dynamics must falsify the retained predictive code.

The system must not trust the compiled code merely because alphabet sizes match.

It must fall back to development/search and construct the new minimum quotient.

### G7 — heterogeneous world
The same frozen kernel must construct a consequence-sufficient quotient for a structurally different hidden transducer without changes to the developmental algorithm.

### G8 — incomplete authority
If the declared future-test table is incomplete, the kernel must return UNKNOWN_AUTHORITY rather than certify global minimality or expressive adequacy.

### G9 — ablation of consequence
If future consequence comparisons are removed, the one-state initial representation must not be authorized to split.

This control distinguishes developmental growth from arbitrary clustering.

## Scientific interpretation

A pass would establish, in a bounded deterministic setting:

> an initially undifferentiated present can be refined into a minimum predictive state language using only intervention-conditioned future consequence, without hand-written domain features.

This is a deterministic finite analogue of causal-state / predictive-state reconstruction, embedded inside the Minimal Developmental Algorithm rather than used as a one-shot clustering rule.

## Claim boundary

A pass does NOT establish:
- metaphysical creation from nothing;
- natural-world ontology genesis;
- continuous or stochastic computational mechanics;
- quantum structure;
- objective uniqueness beyond the declared test universe;
- autonomous invention of the verifier or intervention alphabet;
- that predictive equivalence is the only valid semantics.

The next boundary after a pass is to relax exact finite consequences into noisy/stochastic futures using predictive rate-distortion / statistical authority, then test on less curated physical simulations and real sensor streams.
