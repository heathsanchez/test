# V8 frozen experiment — P-224 root-sign quotient / P-256 quadratic-twist contrast

Date 2026-10-17 NZ. Parent V7b qualified head `130c68ef2165867bc8bba1738f9354cf830fac6a`, run #38992150553. Branch isolated. V7b source-choice results preserved.

## New question (different from brute-force or historical origin)
If the NIST curve-generation relation `c*b² ≡ -27 mod p` admits b and -b, does sign selection affect mathematical curve identity/point-count eligibility on P-224 versus P-256? Does recognizing the equivalence let us avoid needless doubled SEA point-counting on P-224?

## Frozen mathematical lemma
For an odd prime p≡1(mod4), -1 is a square: choose u∈Fp with u²=-1. For all a,b∈Fp and nonsingular E_b:y²=x³+a*x+b, the map φ:E_b→E_{-b} defined by (x,y)↦(-x,u*y), φ(O)=O is an invertible elliptic-curve group isomorphism. Its inverse is (X,Y)↦(-X,u^{-1}Y). Algebraic equation proof: (u*y)²=−(x³+a*x+b)=(-x)³+a*(-x)−b. Group preservation follows from field-curve coordinate change of Weierstrass curves (not a new Lean theorem). In particular, their cardinalities and primality status agree; no separate SEA for both signs is needed for p≡1(mod4).

For p≡3(mod4), no such u belongs to Fp (Euler's criterion for −1). The b,−b curves instead form a nontrivial quadratic-twist relation when nonsingular, with traces opposite and #E_b+#E_{−b}=2(p+1). Do not claim they have equal cardinalities; previous V5 certified candidate-876 high-root prime, low-root composite.

## Frozen executable gates
1. Fetch p,a,b from original public OpenSSL NIST P-224 and P-256 named parameters; verify SHA1 seed c relation exactly, match V6 pinned data. No new coefficient policy speculation.
2. Verify p224 %4=1, p256 %4=3 and p224 u²≡−1 using first small quadratic nonresidue (deterministically discovered without target-specific u).
3. Independently generate ≥32 exact points on original P-224 E_b using modular Tonelli sqrt; transform with φ, check E_{−b}, inverse map, and 16+ nontrivial addition/negation pairs under independent group law.
4. Negative control: no quadratic-root −1 over P256 (Euler), and three invalid u candidates fail to map suitable P-256 point; do not assert impossibility beyond the exact Euler criterion.
5. Reconcile existing V7 FreeLIP P224 sign mismatch as isomorphism / no prime-order distinction, vs V5 P256 twist with different prime/composite orders. No historical root-selector recovery claimed and no assertion of actual NIST cryptographic weakness.
6. Commit immutable code and report on isolated branch, run the test in independent GitHub Actions, archive result and evidence. Status only WARRANTED_EXACT_ALGEBRA_BOUNDED after external run; abstract mathematical lemma is a paper-and-code proof, NOT Lean-kernel certification.
7. Next residual remains independently explained P224 pre-7026 selection history or dated original ECC source; do not increase blind seed sweeps.

No changes to original V1–V7b branch, no outside repo writes or production deployment.
