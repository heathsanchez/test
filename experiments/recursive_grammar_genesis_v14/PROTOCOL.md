# Recursive Grammar Genesis V14 — Frozen Protocol

## Dependency

V14 begins one level above V13.

Pinned lower-layer result:

- V13 branch: `generated-predictive-phrases-v13`
- V13 successful run: `34750329193`
- V13 head: `1bb149700d33dc54de93412e915b73eb26a646c7`
- V13 verdict:
  `VERIFIED_GENERATED_PREDICTIVE_PHRASE_GENESIS_SELECTION_COMPILATION_AND_REUSE`
- V13 artifact SHA-256:
  `8f88f21d04b292f402dc64a885ea8943935a6938b33618d24529d0f170f7c52c`

V13 established that a consequence-earned composite phrase can be compiled into an anonymous reusable atom.

V14 asks what happens next.

## Question

Given only already-verified anonymous phrase atoms, can recurring phrase-of-phrase structure earn a new grammar rule, with no hand-written higher-order phrase boundaries or grammar templates?

The target is not natural language.

The target is the smallest next developmental step:

    verified phrase atoms
        -> recurring compositions of phrase atoms
        -> anonymous grammar rule
        -> grammar rule may itself contain an earlier grammar rule
        -> compiled hierarchical grammar reduces future construction cost.

This is a bounded straight-line grammar / grammar-compression experiment embedded in the Minimal Developmental Algorithm.

## What is primitive to V14

The grammar learner receives only:

1. a finite set of verified anonymous phrase atoms;
2. each atom's exact lower-level expansion and provenance;
3. a finite corpus of independent episodes, each an ordered sequence of phrase-atom identifiers;
4. exact concatenation;
5. an external verifier for complete lower-level expansion / consequence preservation;
6. a finite construction budget.

No phrase-of-phrase rule is supplied.

No `REPEAT`, `LOOP`, `PERIOD`, `PAIR`, `BLOCK`, or named grammar schema is primitive.

## Verified phrase atom admission

A phrase atom is admissible only if it carries:

- an anonymous content-addressed atom identifier;
- exact primitive expansion;
- at least two independent provenance origins;
- a complete verification flag/certificate for the declared lower interface.

This deliberately treats V13 phrase genesis as a certified lower-layer dependency rather than re-proving it inside every V14 trial.

## Grammar representation

A grammar rule is:

    N -> X Y

where X and Y are currently admitted tokens.

A token may be:
- a verified phrase atom; or
- a previously admitted grammar nonterminal.

Therefore the only higher-order constructor is binary composition.

Rules are anonymous and content-addressed.

A rule retains:
- exact right-hand side;
- recursively exact primitive expansion;
- independent support episodes;
- acquisition cost;
- compression gain;
- provenance.

## Candidate generation

Candidate rules are not hand-written.

At each developmental step, enumerate every adjacent token pair occurring in the currently encoded independent episodes.

For each pair c = (X,Y), compute:

- total non-overlapping replacement opportunities;
- number of distinct supporting episodes;
- exact description-length gain.

A candidate is promotion-eligible only if:

1. it appears in at least two independent episodes;
2. replacing its occurrences is semantics-preserving under exact expansion;
3. its grammar description has strictly positive compression gain.

No semantic label influences candidate generation.

## Cost

Corpus cost before a rule:

    C = total encoded token count + sum(rule_rhs_token_count)

Every binary rule definition costs 2 tokens.

If a pair occurs m non-overlapping times, introducing the rule saves m encoded tokens and costs 2 definition tokens.

So direct gain is:

    gain = m - 2.

A rule is eligible only when gain > 0.

This is an explicit bounded MDL-style retention criterion:
structure must pay for itself.

## Developmental algorithm

The governing process remains:

    EXECUTE
    -> VERIFY
    -> DIAGNOSE
    -> CONSTRAIN
    -> RESTRUCTURE
    -> CHOOSE
    -> COMPILE
    -> UPDATE

### EXECUTE
Encode the corpus with the current grammar.

### VERIFY
Check exact recursive expansion and external consequence preservation.

### DIAGNOSE
Measure residual repeated pair structure and future construction cost.

### CONSTRAIN
Generate all adjacent-pair rule candidates from the current encoded corpus.

### RESTRUCTURE
Keep only candidates with:
- independent support >= 2 episodes;
- exact semantic replay;
- positive description-length gain.

### CHOOSE
Select maximal gain.
If several behaviorally distinct candidates have equal maximal gain, preserve a frontier rather than arbitrarily selecting by name.

### COMPILE
Reify the selected anonymous binary rule.

### UPDATE
Replace non-overlapping occurrences, then repeat over the new token alphabet.

Because nonterminals enter the token alphabet, later rules may contain earlier rules.

That is the V14 recursive/hierarchical step.

## Required post-freeze gates

### R1 — no higher grammar supplied
Frozen core contains only:
- verified lower phrase atoms;
- binary concatenation;
- generic adjacent-pair enumeration.

No challenge-specific pair or phrase-of-phrase rule appears in the frozen core.

### R2 — first grammar rule earned
Two or more independent episodes contain repeated lower phrase-atom structure.

The first promoted rule must:
- be generated from observed adjacent pairs;
- have independent support >= 2;
- have positive compression gain;
- preserve exact lower expansion.

### R3 — phrase becomes grammar token
After R2, its nonterminal must participate in subsequent candidate generation exactly like a lower phrase atom.

### R4 — hierarchical rule genesis
A later promoted rule must have at least one nonterminal on its right-hand side.

Its fully expanded primitive action sequence must equal direct lower-level concatenation.

### R5 — no direct hand-written long phrase
The successful hierarchical construction must be reached through repeated binary rule promotion.

The frozen kernel may not insert the final long expansion directly.

### R6 — causal warm reuse
On an unseen held-out episode built from the same verified phrase atoms:

- warm grammar encodes the target within a tight construction budget;
- cold no-grammar encoding exceeds the same budget;
- cold with relaxed budget can construct by direct concatenation;
- ablation of the higher-level rule restores the tight-budget failure.

### R7 — lower-rule ablation
If the lower rule used inside a higher rule is removed, the higher rule becomes invalid/non-replayable rather than silently retaining a dangling dependency.

### R8 — wrong structure not forced
A same-alphabet held-out episode with different ordering must not be falsely recognized as the learned hierarchical phrase merely because atom counts match.

### R9 — heterogeneous grammar
The same frozen grammar learner must induce a different rule hierarchy from a structurally different independent corpus.

### R10 — single-example control
A repeated pair appearing many times in only one episode must not compile.

Independent recurrence is required.

### R11 — hierarchy ablation
If grammar rules are forbidden from appearing as tokens in later rule candidates, the lower rule may still compile, but the higher rule must not.

Under the frozen tight budget this must expose a typed insufficiency.

### R12 — semantic replay / authority
If a supplied lower phrase atom lacks complete verification/provenance authority, return `UNKNOWN_AUTHORITY`.

### R13 — no positive-gain control
If every recurring pair fails the positive-gain criterion, no grammar rule is compiled.

## Transfer / retention claim

A V14 pass establishes only:

> Given already-verified phrase atoms, a bounded generic binary grammar compressor can reify recurring phrase-of-phrase structure into anonymous hierarchical rules, and those rules can causally reduce future construction cost while remaining exactly replayable to the lower semantics.

## Claim boundary

A pass does NOT establish:

- natural-language grammar;
- parameterized variables or universally quantified schemas;
- syntax-to-human-semantics grounding;
- context-sensitive grammar;
- stochastic grammar induction;
- unrestricted recursion;
- that binary adjacency is the final primitive;
- designerless choice of the MDL cost;
- autonomous invention of the verifier.

The next boundary after a pass is **parametric grammar genesis**:

    from literal rule
        N -> P Q
    to a consequence-earned schema
        F(X,Y) -> X Y X Y ...

without supplying the variable/template pattern in advance.
