# LKA Semantic Law Atlas v0

Status: READ-ONLY DEVELOPMENT MAP. This document does not grant checker authority.

Pinned sealed checker: f45b49a6989c09317635c790615ca63c617c84c7
Pinned Arena authority: f5e1bce6e2dc9c60479b3001b76e01722b403799
Atlas run: 35688135655
Atlas artifact: 10677259351
Artifact digest: sha256:269c1d9468966ec1804078f0017085c8615abfa587712de77430be3703260529

## 1. Raw future-corpus result

Tutorials 042-141 were generated from the pinned Arena source and replayed through sealed G15 without changing checker, formal, evidence, Cargo, or trusted runtime files.

Across the 100 future cases:

- 13 already match their expected verdict.
- 59 remain UNKNOWN.
- 18 currently ERROR at the parser boundary.
- 10 are conclusive mismatches.

The mechanically observed first-occurrence structural frontier after sealed tutorial 041 is:

- 043: equality family
- 043: indices
- 043: recursor rule-K metadata
- 044: recursive inductive
- 083: projection expression
- 101: reflexive inductive
- 102: literal / natVal expression
- 104: proof irrelevance
- 108: eta
- 126: quotient family / quot declaration

This frontier is descriptive only. A first appearance is not authority.

## 2. Already implied by the current closure

Sealed G15 already matches future tutorials:

48, 62, 63, 64, 65, 66, 67, 117, 118, 132, 139, 140, 141.

These are useful closure probes. They show that some later tests are already consequences of earlier earned mechanisms and do not require a new capability.

Notable examples:

- 062-067: existing Empty/Bool/TwoBool/And/Prod/PProd recursor types are already checkable from retained opaque signature authority.
- 117-118: two negative recursive-occurrence examples are already rejected by existing structure.
- 132 and 139: some name-collision forms are already rejected.
- 140-141: the current authority discipline already rejects theorem use of unsafe/partial dependencies in these examples.

## 3. Conclusive mismatch audit

The ten future conclusive mismatches are:

44, 45, 70, 71, 80, 82, 95, 107, 121, 122.

Nine of these are in the recursive/indexed-inductive dependency basin:

44 natDef
45 rbTreeDef
70 nRec
71 rbTreeRef
80 nRecReduction
82 RBTree.id_spec
95 projDataIndexRec
121 rTreeRec
122 rtreeRecReduction

The remaining mismatch is:

107 proofIrrelevanceUnderBinder

Interpretation: unsupported semantics are not always remaining epistemically UNKNOWN. In the recursive basin, older narrow inductive handlers can classify a broader recursive neighbor as REJECT. This is inconsistent with the later G12-G15 envelope discipline, where recursive/indexed/nested/unsafe dimensions outside earned authority are deliberately UNKNOWN.

Candidate meta-law:

UNSUPPORTED SEMANTIC DIMENSION => UNKNOWN,
unless the malformed claim lies inside an already recognized authority envelope.

This should be tested as a zero-authority boundary repair before allowing future broad semantic growth.

The proof-irrelevance-under-binder mismatch is a separate conversion residual: structurally different proof applications are currently refuted before proof irrelevance is available.

## 4. Parser frontier

All 18 ERROR cases are concentrated around only two new raw export forms:

- projection expressions beginning at 083
- natVal literal expressions beginning at 102

Structure eta at 112 also reaches the projection parser frontier.

This suggests parser completion is small and orthogonal to semantic authority. Parsing proj and natVal should preserve UNKNOWN until their semantic laws are independently earned.

## 5. Candidate semantic basis

Reading the tutorial organization together with the structural atlas suggests the following candidate basis. These are hypotheses for development, not pre-authorized rules.

### L0. Nullary singleton law
First stress case: 042 PUnit.

Dimensions:
- one level parameter
- zero term parameters
- one nullary constructor
- one motive/minor/rule
- singleton/unit-like shape

Purpose: test whether G15 generalizes from binary products to compositional inductive shape.

### L1. Indexed dependent inductive law
First case: 043 Eq.

Dimensions:
- parameter plus index telescope
- dependent constructor result
- recursor indices
- rule-K metadata

Likely first genuinely new coordinate beyond G15.

### L2. Recursive inductive / positivity law
First positive case: 044 N.
Key controls: 054, 055, 056, 057, 117, 118, 119, 120.

Dimensions:
- recursive occurrences
- strict positivity
- reduction in positive constructor-argument positions
- no illicit reduction of constructor head shape
- later reflexive occurrences behind arrows

### L3. General inductive well-formedness law
Cases 046-061.

Sub-obligations:
- inductive type must be a sort
- declaration level parameters unique
- parameter telescope arity/coherence
- constructor parameter/result agreement
- constructor universe-instance agreement
- recursive occurrence not hidden in forbidden index/negative positions
- constructor field universe admissibility

This is likely a descriptor-validation layer rather than one family classifier.

### L4. Elimination / recursor admissibility law
Cases 062-077.

The first six cases are already implied by current authority. New residuals begin with PUnit, Eq, recursion, and Prop elimination restrictions.

Sub-obligations:
- derive recursor rather than trust export metadata
- motive/minor/rule shape
- Prop elimination restrictions
- singleton elimination into Sort
- direct-index visibility requirement for sort elimination

### L5. Iota computation law
Cases 078-082.

Dimensions:
- recursor reduction on constructor
- recursive hypotheses in recursive eliminators
- indexed recursive reduction

This should compile from verified recursor rules rather than create separate per-family reducers.

### L6. Projection law
Cases 083-098.

Sub-obligations:
- parse projection expressions
- structure membership and field bounds
- projection type derivation
- propositional-structure data/proof restrictions
- dependency barrier for Prop projections
- projection reduction

### L7. Rule K reduction law
Cases 099-101.

Rule K belongs only where the inductive/recursor metadata warrants it. Eq is the primary positive case; Acc is a negative control.

### L8. Literal law
Cases 102-103.

Sub-obligations:
- parse natVal
- Nat literal typing
- literal reduction/equality with Nat constructors

### L9. Proof irrelevance law
Cases 104-107.

All inhabitants of a proposition are definitionally equal, including after WHNF and under binders. The 107 mismatch shows this must be recognized before structural application comparison can produce a false REJECT.

### L10. Eta family
Cases 108-116.

This is at least three distinct laws:
- unit-like eta, restricted to nonrecursive nonindexed unit-like inductives
- structure eta, restricted to nonrecursive nonindexed structures
- function eta, including dependent Pi eta

Do not collapse these merely because the tutorial section groups them.

### L11. Reflexive inductive law
Cases 117-125.

Sub-obligations:
- distinguish forbidden negative/index occurrences from permitted reflexive occurrences behind arrows
- generate/validate recursors for reflexive inductives
- preserve absence of structure eta for Acc
- recursor reduction

### L12. Quotient primitive law
Cases 126-131.

A genuinely primitive kernel family:
- Quot.mk
- Quot.ind
- Quot.lift
- Quot.sound
- lift/ind reduction

This should remain separate from ordinary inductive derivation.

### L13. Name authority law
Cases 132-139.

One global uniqueness/reservation law may cover:
- duplicate definitions
- inductive/definition collisions
- constructor collisions
- recursor collisions
- required recursor naming
- generated-name reservation

Current closure already rejects cases 132 and 139, suggesting the remaining cases may be completion of one environment-level invariant rather than new semantic families.

### L14. Safety authority law
Cases 140-141.

Current G15 already matches both examples. Treat as an already-earned consequence unless broader Arena evidence exposes a residual.

## 6. Candidate dependency graph

A plausible high-leverage development order is:

PUnit
  -> indexed Eq
  -> general inductive descriptor
  -> recursion + positivity
  -> elimination/recursor admissibility
  -> iota

In parallel, orthogonal parser/definitional-equality branches can proceed:

projection parser -> projection semantics -> structure eta
natVal parser -> literal semantics
proof irrelevance -> unit/structure/function eta checks
quot primitive
name-authority completion

Reflexive inductives depend on the recursive/positivity layer and should come after ordinary recursion is stable.

## 7. Architectural interpretation

The emerging internal object is probably not BinaryProductSortLaw.

A better candidate coordinate system is:

InductiveLaw =
  authority envelope
  + result-sort law
  + parameter telescope
  + index telescope
  + constructor shape
  + occurrence/positivity policy
  + elimination policy
  + computation policy

G15 has already shown that representation may be generalized internally without broadening external authority.

G16 should therefore test whether a new descriptor coordinate can be added through the retained skeleton, not whether a new fourth bespoke classifier can be written.

## 8. ETP-style discipline

Use the same separation as the ETP future-set work:

1. Compile what the interface already forces.
2. Quotient representations that are consequence-equivalent.
3. Mine only the residual distinctions.
4. Treat numerical or syntactic patterns as shadows until structurally explained.
5. Never let the discovery atlas itself grant authority.

The tutorial corpus may propose the law basis. Only formal semantics, exact derivation, falsification, sealed-oracle replay, and external qualification may promote a law.
