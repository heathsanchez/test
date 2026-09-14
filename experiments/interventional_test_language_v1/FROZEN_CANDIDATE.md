# Interventional Test-Language Expansion V1 — Frozen Candidate

**Status:** FROZEN BEFORE TEST  
**Date:** 2026-09-14

## Candidate

The state–test/consequential-information core must not identify observational equivalence with universal equivalence.

If two candidate worlds have identical authorized observational consequences but differ under an authorized intervention, then:

1. an observation-only test family legitimately yields EQ **only in observational scope**;
2. if protected consequence requires interventional behavior, the observation-only language is inadequate;
3. adding interventions to the test family may split the worlds without changing the evaluation/kernel law itself.

## Frozen adversary

Two binary structural causal models share the same observational distribution:

- Model A: U ~ Bernoulli(1/2), X=U, Y=X.
- Model B: U ~ Bernoulli(1/2), Y=U, X=Y.

Both observe only (X,Y)=(0,0) or (1,1), each with probability 1/2.

Under intervention do(X=0):

- A forces Y=0;
- B leaves Y=U and therefore Y is Bernoulli(1/2).

Under do(Y=0), the asymmetry reverses.

## Predictions

- observational signature(A) = observational signature(B);
- interventional signature(A) != interventional signature(B);
- no interventional expansion is warranted if the protected scope is observational only;
- expansion becomes warranted when protected consequence includes intervention response.

## Falsifier

V1 fails if:
- observational data alone distinguishes the frozen pair;
- interventions fail to distinguish them;
- the distinction requires changing the kernel law rather than expanding the authorized test family;
- observational-only scope is forced to retain a causal distinction it cannot warrant.
