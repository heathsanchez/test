# Finite Transition-Relation Genesis V45 — Frozen Protocol

## Question

Can determinism and totality themselves be removed as supplied properties of interventions?

V45 receives only:

- a finite opaque state set X;
- for each opaque action token and source state, the complete set of possible successor states;
- verified consequence classes over those actions.

An action row may have:

- exactly one successor;
- no successor;
- several successors.

The scientific kernel therefore receives arbitrary finite transition relations R ⊆ X×X rather than functions.

The hidden challenge pack is committed only after this scientific core is frozen.

## Generic relational substrate

One action is represented extensionally as a binary relation on X.

The scientific kernel provides only generic relation-algebra operations:

- identity relation;
- ordinary relational composition;
- closure of generators under composition;
- comparison/equality of finite relations;
- weak connectivity of observed transition edges.

No deterministic, partial, stochastic, or nondeterministic model family is proposed.

## Derived local relation type

For any generated relation R, inspect the cardinality of each successor set R(x).

The kernel derives:

### TOTAL_FUNCTION

Exactly one successor for every x.

### PARTIAL_FUNCTION

At most one successor for every x, and at least one source has no successor.

### NONDETERMINISTIC_RELATION

At least one source has more than one successor.

These labels summarize the relation itself after it has been observed/generated.

They do not select different inference mechanisms.

## Generated relation monoid

For each verified action class C_i, close the observed relations in that class under relational composition while adjoining identity:

    M_i = <C_i>.

Close all observed action relations together:

    M = <all actions>.

For every class and for M, record only algebraically forced statistics:

- closure cardinality;
- counts of total functions;
- counts of partial functions;
- counts of genuinely nondeterministic relations;
- successor-branching spectrum;
- domain-size spectrum;
- image-size spectrum;
- idempotent count;
- empty-relation count.

Thus determinism, partiality, and nondeterminism can coexist within one generated closure.

## Interaction between verified action classes

For multiple consequence classes, V45 computes:

- pairwise commutation of the class relation monoids;
- pairwise identity-only intersection;
- product of class-monoid cardinalities;
- the image obtained by multiplying one relation from each class monoid;
- whether those multiplication coordinates are unique;
- whether that image spans the full generated relation monoid.

No Cartesian state representation is searched.

## Global classifications

### DERIVED_DIRECT_RELATION_COMPLEMENTARITY

Returned only if:

- class relation monoids commute pairwise;
- pairwise intersections contain identity only;
- multiplication coordinates are unique;
- the multiplication image equals the full generated relation monoid;
- observed transition edges weakly connect the state space.

The classes may contain total functions, partial functions, nondeterministic relations, or mixtures.

### UNDERRESOLVED_MULTIPLE_ACTION_COMPONENTS

The same internal direct algebra holds, but current observed transitions leave several disconnected state components.

### COUPLED_TRANSITION_RELATIONS

Returned when the direct composition law fails—for example because class multiplication is nonunique even if cardinalities and commutation look tempting.

### UNDECOMPOSED_SINGLE_CLASS

If verified consequence supplies only one action class, the kernel does not invent internal components.

## Generic multiplicity ablations

The same frozen kernel supports only two generic authority restrictions for ablation:

- a lower bound on the number of successors per source;
- an upper bound on the number of successors per source.

These are not alternative model types.

They test whether empty successor sets or branching successor sets are actually necessary.

Examples:

- maximum successors = 1 forbids genuine nondeterminism but still allows partial functions;
- minimum successors = 1 forbids partiality but still allows total deterministic and total nondeterministic relations.

If observed authority violates such a bound, the kernel returns CERTIFIED_SUCCESSOR_MULTIPLICITY_BOUND_INADEQUACY before algebraic construction.

## Primary post-freeze challenge family

Only after freeze, the hidden harness will instantiate:

- a rich one-class world whose relations are all total deterministic functions;
- a one-class partial-function world containing empty successor sets but no branching;
- a one-class genuinely nondeterministic world with branching but no empty successor sets;
- a two-class nondeterministic world over a hidden three-degree generator, leaving one unobserved degree and therefore multiple weak components;
- the corresponding three-class nondeterministic world, which should become directly complementary;
- a mixed three-class world containing one deterministic reversible class and two genuinely nondeterministic classes;
- a coupled flip/branching-relation world acting on the same hidden degree; the class monoids commute and intersect only in identity, but class multiplication is not unique, so the kernel must refuse a false decomposition;
- independent opaque-state relabellings;
- consequence-label relabellings.

The hidden harness may use convenient coordinates internally. The frozen kernel never receives them.

## Frozen gates

R1. Frozen scientific core remains byte-identical.

R2. Deterministic one-class control remains UNDECOMPOSED_SINGLE_CLASS and every generated relation is TOTAL_FUNCTION.

R3. Partial one-class control remains UNDECOMPOSED_SINGLE_CLASS; its closure contains PARTIAL_FUNCTION relations, no NONDETERMINISTIC_RELATION, and at least one source-empty relation row is necessary.

R4. Nondeterministic one-class control remains UNDECOMPOSED_SINGLE_CLASS; its closure contains a genuine NONDETERMINISTIC_RELATION, no PARTIAL_FUNCTION, and branching degree 2 is derived.

R5. Two independent nondeterministic action classes generate two order-2 class relation monoids and an order-4 full relation monoid, but leave two weak state components and therefore UNDERRESOLVED_MULTIPLE_ACTION_COMPONENTS.

R6. Adding the third independent nondeterministic class yields three order-2 class relation monoids, an order-8 full relation monoid, one weak state component, unique class multiplication, and DERIVED_DIRECT_RELATION_COMPLEMENTARITY.

R7. Mixed deterministic/nondeterministic classes can still satisfy DERIVED_DIRECT_RELATION_COMPLEMENTARITY; determinism is not required for independence.

R8. In the mixed world, one class closure contains only total functions while the other class closures contain genuine branching relations.

R9. The coupled flip/branching control has commuting order-2 class monoids with identity-only intersection and cardinality product 4, but multiplication coordinates are nonunique and the full relation monoid has order 3; classification must be COUPLED_TRANSITION_RELATIONS.

R10. Opaque-state relabelling preserves every algebraic profile, weak-component count, and classification.

R11. Consequence-label relabelling preserves every algebraic profile and classification.

R12. Removing the third nondeterministic class from the full three-class generator restores the two-class underresolved algebra.

R13. Maximum successor multiplicity 1 preserves deterministic and partial controls but rejects every genuinely nondeterministic world before algebraic construction.

R14. Minimum successor multiplicity 1 preserves deterministic and nondeterministic controls but rejects the partial world before algebraic construction.

R15. Incomplete authority remains UNKNOWN_AUTHORITY and verifier ablation performs zero algebraic construction.

R16. The frozen authority/kernel contains no requirement that each action be total, functional, or single-valued; hidden challenge-family names and old graph/site/channel vocabulary are absent from the frozen executable kernel.

## Claim boundary

A pass would not establish stochastic or nondeterministic inference from ordinary finite samples.

V45 still supplies:

- a finite opaque state set;
- complete relational authority: the full successor set for every observed state/action pair;
- verified action classes;
- exact relational composition as the algebraic substrate.

What a pass can establish is narrower:

> determinism and totality need not be supplied as intervention primitives. Given complete finite transition relations, the system can derive whether observed/generated dynamics are total functions, partial functions, genuinely branching relations, or mixtures, and can distinguish independent relational dynamics from coupled ones by their composition law.

If V45 passes, the remaining handhold is complete extensional relational authority. The next frontier is incomplete/empirical transition evidence: repeated samples or frequencies from which the system must decide whether a deterministic relation, nondeterministic support relation, probability kernel, or UNKNOWN is actually justified.
