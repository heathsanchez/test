# V25 — SAIR Bounded-Model Adequacy Escalation

## Frozen residual from V24

`ORDER2_BEHAVIORAL_ADEQUACY_DOES_NOT_GENERALIZE_STRONGLY_TO_HARD3`

V24 passed its narrow raw-domain bridge gate, but the frozen policy fell from 89.4% development accuracy to 56.75% on held-out `hard3`. Exact Fin-2 behavior helped over syntax-only, but only by 2 percentage points on the held-out source.

## Question

Does increasing verifier-visible behavioral resolution—without adding semantic developmental labels—produce a materially stronger raw-domain adequacy map on the same external SAIR split?

## Change from V24

Everything from V24 remains frozen. V25 adds only anonymous bounded-model ports produced by exact SMT search for order-3 countermodels and reverse-countermodels.

For each raw SAIR implication, Z3 is asked whether there exists a `Fin 3` magma satisfying the hypothesis while violating the target, and symmetrically for the reverse implication. Any SAT witness is independently re-evaluated by the raw equation evaluator before being admitted as an observation.

No answer label is used to compute these ports.

## Frozen split

- develop: `normal + hard1 + hard2`
- held out: `hard3`

## Gates

1. all V24 raw/external split conditions remain true;
2. every SMT witness is independently rechecked;
3. the minimum policy using order-3 behavioral ports beats the frozen V24 held-out accuracy 0.5675;
4. it beats syntax-only;
5. removing order-3 ports lowers held-out accuracy;
6. shuffling order-3 verifier outcomes lowers held-out accuracy.

Umbrella: `SAIR_BOUNDED_MODEL_ADEQUACY_GATE`.

## Boundary

Finite bounded-model behavior is still not full Lean adequacy. This test asks only whether a higher-resolution verifier trace repairs the natural-domain residual exposed by V24.