# Generated Predictive Phrases V13 — Frozen Protocol

## Question

Can a predictive "phrase" be constructed compositionally from atomic interventions, rather than selected from a hand-written phrase list, and can such a phrase become a reusable anonymous unit only after verified consequence earns it?

V12 established bounded predictive causal-state genesis from an undifferentiated present, but its candidate future tests were supplied as a finite list. V13 removes that hand-written phrase vocabulary.

The learner receives only:
- an anonymous finite action alphabet A;
- an anonymous finite observation alphabet O;
- ordered encounter histories;
- a finite maximum phrase length L;
- an external oracle/table for the observation consequence of any action string of length <= L after each admitted history;
- finite completeness authority over that declared language.

The learner is **not** supplied any multi-action test as a primitive.

All multi-action tests must be generated from atomic actions using one constructor:

    CONCAT : Phrase x Phrase -> Phrase

with atoms:

    ATOM(a)  for a in A.

The developmental algorithm remains:

    EXECUTE -> VERIFY -> DIAGNOSE -> CONSTRAIN
    -> RESTRUCTURE -> CHOOSE -> COMPILE -> UPDATE

and the standing law remains:

    maintain the smallest present sufficient for verified consequence;
    change it only when consequence proves inadequacy;
    preserve incomparable minimal repairs;
    let independently verified future consequence select;
    compile what transfers;
    return UNKNOWN at the warrant boundary.

## Scientific relation to V12

V12:
    future tests were already present as candidate phrases.

V13:
    only atomic actions exist initially;
    longer tests must be constructed by CONCAT.

Therefore a successful length-k predictive test is evidence for phrase genesis only if:
1. its expansion contains k atomic actions;
2. it was generated from atomic actions by the frozen constructor;
3. it was not supplied as a primitive challenge item;
4. it is independently verified against complete future consequence;
5. its use reduces the minimum predictive code;
6. after recurrence/transfer it may be compiled into an anonymous macro atom;
7. cold and ablation controls restore construction/search cost.

## Phrase semantics

A phrase p = (a_1,...,a_k) denotes an intervention test.

For history h:

    outcome(h,p)

is the future observation string produced by applying p after h.

Two histories are equivalent under phrase set P iff:

    h ~_P h'
    iff
    for every p in P,
    outcome(h,p) = outcome(h',p).

The complete bounded predictive quotient uses **all generated phrases** up to length L:

    Lang_L(A) = union_{1 <= k <= L} A^k.

No domain feature vocabulary participates.

## Phrase generation

The frozen grammar is:

    Phrase ::= ATOM(a) | CONCAT(Phrase, ATOM(a))

Generation is breadth-first by expansion length.

No semantic name is attached to a phrase.

A phrase carries:
- anonymous interface type;
- exact atomic expansion;
- structural length;
- consequence signature over admitted histories;
- provenance;
- compilation evidence when promoted.

## Development from obstruction

### EXECUTE
Start from no active predictive phrases:

    P_0 = {}

so every history is one state.

### VERIFY
Compare the current quotient against the complete bounded quotient induced by Lang_L(A).

### DIAGNOSE
Find histories h1,h2 identified by current P but separated by complete future consequence.

### CONSTRAIN
Generate phrases breadth-first until at least one generated phrase separates h1,h2.

### RESTRUCTURE
The lawful local repairs are exactly the shortest generated separating phrases.

### CHOOSE
Preserve behaviorally distinct equal-cost repairs.
Independent qualification may later eliminate candidates.

### COMPILE
A phrase or phrase-set is compilable only after independent repeated verification.

### UPDATE
Compiled phrases become anonymous macro atoms for later construction/replay, but retain exact expansion and verifier replay.

## Global minimum / idiomaticity

Expressibility is not enough.

The final code must be globally minimum in the declared finite language under lexicographic cost:

    (# phrases, total atomic expansion length).

The exact global minimum is found by reducing phrase selection to a complete minimum set-cover problem over consequentially distinguishable history pairs.

For each pair of histories separated by the complete bounded quotient, a phrase "covers" the pair iff it produces different outcomes on them.

A predictive code is complete iff its phrases cover every consequentially distinguishable pair.

This allows exact minimum-code verification without enumerating every phrase subset.

This is the V13 analogue of "idiomaticity":
among all expressively adequate phrase sets, retain the smallest verified phrase vocabulary.

## Required post-freeze gates

### P1 — atoms only at genesis
The primitive phrase basis contains only length-1 actions.
No multi-action phrase occurs in the frozen basis/kernel as a supplied semantic primitive.

### P2 — blank present to generated phrase
On a hidden disturbance world, the learner starts with one representational class.
Certified obstruction forces phrase construction.
At least one required phrase must have length > 1 and must be generated by CONCAT.

### P3 — generated contraction
On the main hidden world, local minimum-change development may accumulate several shorter phrases.
Exact global minimization must then contract them to a smaller predictive vocabulary containing a generated composite phrase.

Target control:
    a single generated phrase of length 7 is sufficient and globally minimum,
    while the local developmental route first accumulates multiple shorter phrases.

The kernel is not told which length-7 phrase is useful.

### P4 — exact minimum proof
All phrases in Lang_L(A) are generated exhaustively.
The set-cover solver must certify the globally minimum predictive code and produce an explicit lower-bound certificate:
- no zero-phrase code is complete;
- no shorter single phrase is complete;
- the discovered phrase is complete.

### P5 — non-canonicity
A separate post-freeze world must produce at least two equal-cost shortest generated separating phrases.
The repair frontier must preserve them.
Independent future consequence then selects one.

### P6 — phrase compilation
The same generated phrase, independently verified on two hidden-state renamings, becomes an anonymous compiled phrase atom containing:
- exact atomic expansion;
- consequence signature;
- provenance;
- interface type.

### P7 — causal phrase reuse
On a third hidden-state renaming:
- warm compiled phrase replay succeeds with zero phrase-acquisition search;
- cold zero-acquisition returns UNKNOWN_PHRASE;
- ablation restores UNKNOWN_PHRASE.

### P8 — wrong-world falsification
A same-interface world with different hidden dynamics must replay-check and falsify the retained phrase if it no longer induces the complete predictive quotient.
The learner must fall back to phrase generation/minimization.

### P9 — heterogeneous transfer
The same frozen phrase grammar/kernel must solve a structurally different hidden transducer.

### P10 — incomplete authority
If the bounded phrase consequence oracle is incomplete, return UNKNOWN_AUTHORITY rather than certify minimality.

### P11 — CONCAT ablation
With CONCAT disabled, only atomic phrases are constructible.
If atoms are insufficient, return certified/typed obstruction or UNKNOWN rather than smuggling in a composite test.

### P12 — consequence ablation
Without future-consequence comparison, no representational split or phrase promotion is authorized.

## Phrasebook interpretation

The experiment borrows only the **layering** idea from a formal phrasebook:

    atomic vocabulary -> typed composition -> recurring useful phrase -> compiled idiom

It does not import Mathlib's mathematical ontology.

A compiled phrase is anonymous and consequence-earned.

Human-readable names, if ever added, are annotations after verification rather than primitives of the learner.

## Claim boundary

A pass establishes only:

> in a bounded deterministic intervention language, a minimum predictive phrase can be generated compositionally from atomic actions, selected by future consequence, and compiled into a causally useful reusable unit.

It does not establish:
- natural-language genesis;
- unrestricted grammar induction;
- human semantics;
- natural-world grounding;
- stochastic/continuous completeness;
- quantum structure;
- that CONCAT is the final irreducible composition law;
- that the learned phrase vocabulary is unique outside the declared finite consequence universe.

The next boundary is recursive phrase grammar:
can compiled phrases participate as atoms in the construction of larger phrases and eventually earn reusable grammar rules without those grammar rules being supplied?
