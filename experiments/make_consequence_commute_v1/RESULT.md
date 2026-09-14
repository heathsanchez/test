# Make Consequence Commute V1 — Result

**Frozen candidate:** `016a7f60d621d9034c47949c0ca37cead56eaed9`  
**Implementation:** `608467958d21f7cade78bdcf58d4219b710c6dfb`  
**Workflow:** `28d1679ca8bae0d033a0f3675695668e72739afa`  
**Run:** 34822398195  
**Job:** 103906720752  
**Artifact:** 10338354699  
**Digest:** `sha256:7270df98e7367120f1153568682cab1456506715d9ddee151b5d184fca5d577c`

## Verdict

```text
PASS 35/35

VERIFIED_OBSERVATION_LANGUAGE_GENESIS_AFTER_CERTIFIED_OBSTRUCTION
VERIFIED_CONSTRUCTOR_LANGUAGE_GENESIS_AFTER_CERTIFIED_OBSTRUCTION
VERIFIED_REALIZATION_CLASS_GENESIS_AFTER_CERTIFIED_OBSTRUCTION
VERIFIED_CONSEQUENCE_PRESERVING_REALIZATION_CLASS_SWITCH
VERIFIED_POST_COMPILATION_CONTRACTION_AND_ABLATION
SURVIVED_MAKE_CONSEQUENCE_COMMUTE_V1
```

## Sequence

### Observation language

The complete initial language contained all seven coordinate-projection probes of arity <=2. Even- and odd-parity worlds were indistinguishable under that entire language.

Only after exhaustive closure certified non-separation was arity 3 admitted. Full tuple-occurrence signatures then separated the worlds exactly and decoded both downstream targets.

### Constructor language

The initial Z4 constructor grammar generated only translation +2, with exact reachable closure {0,2}. Both required targets were odd and unreachable.

Exhaustive single-translation meta-search found exactly two minimal repairs: +1 and +3. Both generate all of Z4 together with +2. The nonunique minimal frontier was preserved rather than tie-broken.

### Realization class

The exact protected membership map was initially represented by two explicit 8-bit tables, 16 bits total.

A later deployment contract imposed an 8-bit representation budget, certifying the current realization class inadequate.

Exhaustive search over all 16 affine GF(2) maps per world discovered unique exact realizations:

```text
E -> (1,1,1,1)
O -> (0,1,1,1)
```

for `f(x)=b xor a1*x1 xor a2*x2 xor a3*x3`.

The two affine mediators require exactly 8 coefficient bits and reproduce all 16 protected membership consequences.

### Contraction and ablation

The old 16-bit table machinery was removed.

All protected membership, world-distinction and navigation consequences replayed successfully using the compact realization plus constructor frontier.

With the tables already absent, exact ablation of the acquired affine mediator restored protected evaluation failure; restoring it restored full protected consequence.

## Claim boundary

This establishes a bounded finite example of one invariant governing:

```text
observation-language growth
constructor-language growth
realization-class growth
consequence-preserving class switch
contraction
```

under frozen finite meta-classes and independently checked consequences.

It does **not** establish unrestricted invention of new observation, constructor or realization algebras outside the declared meta-languages.

The strongest justified interpretation is:

> Within the declared finite meta-language, certified inability to make protected consequence commute forced expansion along three different developmental axes, and once a cheaper lawful mediation existed the old machinery could be dissolved.
