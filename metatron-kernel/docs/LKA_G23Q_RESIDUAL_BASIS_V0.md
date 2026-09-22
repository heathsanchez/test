# LKA G23Q Residual-Basis V0

Status: READ-ONLY DISCOVERY EXPERIMENT

Pinned checker authority: G23 at 7975697a23091ee72abbfe6e68042f0e079f8738
Pinned Arena source: f5e1bce6e2dc9c60479b3001b76e01722b403799

This experiment may guide the next rewrite but grants no checker authority.

## Question

Can the untouched tutorial suffix be represented as a finite consequential residual, and can a small anonymous structural observation basis separate every pair that the current G23 checker still identifies but the frozen Arena target distinguishes?

For suffix states x,y define:

- current(x) = G23 exit code;
- target(x) = Arena expected exit code.

The residual relation is

    U = {{x,y} : current(x)=current(y) and target(x)!=target(y)}.

A candidate observation g separates {x,y} when g(x)!=g(y).

The experiment asks for an exact minimum set of candidate observations whose union separates every pair in U.

This is the finite discovery analogue of Metatron.ResidualBasis.CoversResidual. It is not a proof that the selected observations are sound Lean kernel laws.

## Frozen candidate-observation grammar

Candidate observations are generated mechanically from anonymous NDJSON structure only.

Allowed families:

1. record / expression / universe / declaration tag counts;
2. name-tree depth histograms, but never literal name strings;
3. Pi-chain, application-spine and lambda-chain depths;
4. bound-variable and universe-argument arities;
5. declaration safety/hint counts and anonymous duplicate-name relations;
6. inductive metadata:
   - number of blocks/types/constructors/recursors;
   - parameter/index/nesting counts;
   - recursive/reflexive/unsafe flags;
   - universe arities;
   - constructor parameter/field counts;
   - recursor parameter/index/motive/minor/K/rule counts;
7. anonymous structural relations:
   - constructor result headed by its owning inductive;
   - constructor result argument count;
   - self occurrence in field domains;
   - definitely negative self occurrence;
   - outer expression forms of type results and constructor fields;
   - direct field-sort level shapes;
8. generic transforms of every allowed observation:
   - raw value;
   - zero / positive test for integers;
   - list length / emptiness / deduplicated set.
9. behavioral observations from already-sealed checker generations:
   - per-generation verdicts on the same untouched suffix case;
   - anonymous verdict-lineage vector;
   - change / conclusive / UNKNOWN / ERROR counts across lineage.
10. deterministic feature-gated G23 operation observations:
   - declarations visited;
   - staged inductive signatures;
   - type judgments;
   - kernel conversions;
   - the anonymous operation-count vector and conversion/type-judgment pressure pair.

Behavioral diagnostics are observations only. The diagnostic build must return
the same verdict as the normal G23 binary on every case or the experiment fails.

Forbidden:

- tutorial filename;
- tutorial ordinal as a candidate observation;
- literal Lean names such as Eq, Nat, PUnit or Quot;
- expected verdict as an observation;
- hand-labelled semantic family names;
- source-line identity;
- hidden mapping from anonymous candidate ID to structural meaning during prediction.

## Blind protocol

1. Generate suffix tutorials 056-141 from the pinned Arena source.
2. Run byte-identical G23 checker on each case.
3. Extract candidate observations with the frozen grammar.
4. Replace case numbers and observation names by deterministic content-independent anonymous IDs.
5. Public prediction input contains:
   - anonymous state ID;
   - current G23 verdict;
   - frozen target verdict;
   - anonymous observation vectors.
6. Hidden reveal contains only:
   - state ID -> tutorial number;
   - observation ID -> structural observation name.
7. Commit to the hidden reveal by SHA-256 before prediction.
8. The predictor computes an exact minimum residual cover using public data only.
9. Reveal verifies the commitment and decodes the selected structural basis.

The target quotient is public, matching Metatron's blind separating-hypergraph design. The hidden information is the semantic interpretation of candidate coordinates.

## Held-out transfer

A deterministic held-out split uses tutorial_number mod 5 = 0.

The exact basis is fit only to training residual pairs. After selection, reveal measures how many held-out residual pairs the same basis separates.

This is a transfer diagnostic, not an authority gate.

## Sham

For every candidate observation independently, values are deterministically rotated inside each current-verdict class. This preserves per-verdict marginal values while destroying case-level semantic alignment.

The same training-basis / held-out test is run on this sham representation.

A useful positive should show real structural coordinates transfer at least as well as sham and preferably with a smaller/equal basis.

## Admission boundary

No checker source, formal semantics, evidence ledger, Cargo manifest or retained fixture may change on this branch.

A positive result licenses only the next experiment:

- design an obligation interpreter whose primitive vocabulary is restricted to independently warranted laws corresponding to selected residual coordinates;
- compare the rewrite against G23 as an executable oracle;
- require zero verdict movement before semantic growth.

It does not license automatic ACCEPT or REJECT of any suffix case.
