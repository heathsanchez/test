# V8: Signed coefficient choices have different mathematical significance on P-224 and P-256

**Scope / status:** Locally executed exact algebraic test (GitHub native CI status separate). This is a verified source-linked *finite computational instantiation* of an elementary general theorem, not a new historical selection algorithm, a Lean-kernel certificate, or an ECDSA cryptanalysis result.

## Parent and precommit

- Parent: `heathsanchez/test@130c68ef2165867bc8bba1738f9354cf830fac6a`, V7b 1997 FreeLIP `zsqrtmod` source-native green [Actions #38992150553](https://github.com/heathsanchez/test/actions/runs/38992150553), evidence artifact #12084749520.
- V8 hypothesis frozen separately *before implementation* in isolated commit [`cdbfc92c`](https://github.com/heathsanchez/test/commit/cdbfc92c0ff3ab4a70ae4e06ba13c839741db424) (`V8_FROZEN_PROTOCOL.md`). V7b's positive 5/5 native rule agreement, 4/5 published root-sign agreement and its P-224 invalid-square timeout are unchanged.
- Standardized values read from original `openssl ecparam -name secp224r1/prime256v1 -param_enc explicit`; original V7 SHA1/source bridge recomputed. Source SHA256 and output geometry retained in `V8_RESULTS.json`.

## The mathematical separator

For odd prime `p` with `p ≡ 1 (mod 4)`, select any `u` satisfying `u² = −1 (mod p)`. On nonsingular short-Weierstrass curves

`E_b : y² = x³ + a*x + b`, `E_{−b} : Y² = X³ + a*X − b`,

the formula `φ(x,y) = (−x, u*y)` (and `φ(O)=O`) is an `F_p` elliptic-curve isomorphism, with inverse `(X,Y) -> (−X,u^(−1)*Y)`. Indeed `Y² = −y² = −x³−a*x−b = X³+a*X−b`. The formula comes from a Weierstrass change of coordinates (take scaling `w=−u`, so `X=w²*x`, `Y=w³*y`); it therefore transports the group law. Consequently both signs yield precisely the same group order and same prime-order eligibility, not merely matching a few sampled points.

P-224's `p ≡ 1 (mod 4)`, so the *published* b and opposite FreeLIP-selected b have isomorphic curves. Their numerical coefficient mismatch remains, but it does **not** distinguish prime-order eligibility. This makes a second point-count test of the opposite P-224 sign redundant and removes a potential false objection to its historical selector: one may have chosen either representation without changing the group.

For P-256, `p ≡ 3 (mod 4)`, so `−1` is not a quadratic residue (Euler criterion). The above base-field isomorphism does not exist, and `E_b, E_{−b}` are quadratic twists with orders summing to `2(p+1)` when nonsingular. The V5 point-counting certificate found prime order for candidate 876's high b and composite for low b. Thus sign matters to *group-order admissibility* on P-256 but **not** on P-224.

## Exact executable gates

- Reused V7 source-derived `zsqrtmod` and NIST/OpenSSL c/b and field checks on P-224 and P-256; zero new general framework.
- P-224 minimal small nonresidue `q=11`; `u=q^((p−1)/4) mod p`, `u²=−1 mod p`, source exact `u = 0xe04ce3d9fc37fa7cfaca1a05af3062ab2cb969e6c198a5e71bdabe19`.
- 64 freshly constructed exact on-curve P-224 points, forward and inverse φ checks; 24 nontrivial addition-pair checks and 12 negation checks against a separate affine group implementation, plus O→O.
- P-256 Euler −1 nonsquare, published generator lies on standardized curve; three intentionally invalid u candidates fail to map it onto E_{−b}.
- Source hashes, stable machine-readable result, and negative controls are emitted. No post-hoc parameter selection or claim about the original NSA code.

## Interpretation / next experiment

**WARRANTED inside exact algebraic field/interface assumptions:** P-224 b/−b are isomorphic and equal-cardinality; the observed 4/5 coefficient-choice mismatch in V7 does not mean a different prime-order acceptance property on P-224. **Still UNKNOWN:** original P-224 seed stopping decisions, original FreeLIP/NSA invocation, P-256 base-point G generation, independent mathematical novelty, and autonomous method advantage.

Next most consequential step is a pre-frozen source-authenticated earlier viable P-224 candidate test or discovery of a historically archived ECC generator call path, not another arbitrary seed sweep. If a P-224 skipped candidate and published target differ, compare a source-grounded predicate at the level of *isomorphism classes*, not arbitrary representative signs.
