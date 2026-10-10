# Collatz V168 — a clocked weighted-renewal identity and adversarial boundary controls

**11 October 2026, NZ. Status: CANDIDATE_ANALYTIC_DUAL + BOUNDED_EXACT_NEGATIVE_CONTROLS. Global Collatz UNKNOWN, no QED.** This isolated experiment extends V165/V166/V167 without silently promoting a spectral inequality. The exact finite controls execute in `research/collatz_v168_renewal_controls.py`. Their CI checks executable arithmetic only; the general mathematics below is elementary derivation requiring separate Lean reification before FORMAL promotion.

## 1. Genuine NEW arithmetic accounting obligation

Use the true shortcut T(2u)=u, T(2u+1)=3u+2 on positive naturals and terminal E={1,2}. Define U_H(n)=1 when the actual source n has NOT hit E by any clock j<=H, and 0 otherwise. Since E is forward-closed, **U_(H+1)(n)=U_H(T(n))** at every n>0.

For any s>1, S_s(H)=sum_{n>=1} U_H(n)/n^s converges absolutely. The COMPLETE true predecessor grammar is 2y plus p(y)=(2y-1)/3 for y=2(mod 3); this p(y) is automatically a positive odd integer for y>=2. Partitioning the source sum gives the exact identity

    S_s(H+1) = 2^(-s) S_s(H)
               + sum_{y>=2, y=2(mod3)} U_H(y) / p(y)^s.

Therefore the **newly terminal-admitted weighted mass** is EXACTLY

    S_s(H)-S_s(H+1)
      = (1-2^(-s)) S_s(H)
        - sum_{y>=2, y=2(mod3)} U_H(y)/p(y)^s >= 0.

This is an actual mass-change identity, unlike V165's same-source population transport. It contains the precise odd-predecessor replenishment that must be controlled. The inequality >=0 is mere certificate monotonicity; NO UNIFORM POSITIVE GAP has been established.

Finite HEIGHT X has a crucial extra boundary: even predecessors y<X/2, odd predecessors p(y)<X with y permitted up to (3X+1)/2. Dropping y>=X is forbidden. The finite exact identity is

    sum_{0<n<X} U_(H+1)(n)/n^s
      = sum_{0<y<ceil(X/2)} U_H(y)/(2y)^s
        + sum_{y=2(mod3), 0<p(y)<X} U_H(y)/p(y)^s.

This is the correct V165-to-V166-to-new-admission compiler, preserving original n and clock and source-height export.

## 2. A quantitative necessary bias for a hypothetical bad class

Suppose B is any nonempty positive future-invariant, terminal-disjoint class: b(n)=b(T(n)) in {0,1}, b(1)=b(2)=0. Write m=min B and S_s(B)=sum_{n in B} n^(-s)>0.

The fixed-class inverse identity and comparison (3/2)^s < (3y/(2y-1))^s <= (3m/(2m-1))^s imply, defining R_s(B)=(sum_{y in B, y=2(mod3)} y^(-s))/S_s(B), that

    rho_s * (1-1/(2m))^s <= R_s(B) < rho_s,
    rho_s=(2^s-1)/3^s.

For s=3/2, rho_s = approximately 0.3518809642. If m>=15, the LOWER bound is strictly larger than 1/3 (at m=15 about 0.334434358). Finite verification of n=1..14 suffices to make m>=15 for a hypothetical actual Collatz bad set; this does not presuppose all-source convergence.

Thus **a hypothetical bad class must carry a specific s-weighted ternary excess**. This is a NECESSARY constraint and a candidate attack surface, not the independently proved anti-concentration estimate that would exclude it.

Cheapest sufficient arithmetic target to test: derive, from true +1 source-height arithmetic rather than from generic invariant-label assumptions, a bound R_(3/2)(B)<=1/3 for any putative actual terminal-disjoint B. This would contradict the necessary bound, but no independent proof of that inequality is currently available. Merely asserting it reformulates the conjecture, as in V157.

## 3. Negative control: exact conditional parity mixing DOES NOT force unique basin

For c odd define T_c(2u)=u, T_c(2u+1)=3u+(3+c)/2. Its parity-word coding on n mod 2^h is a bijection for every finite h, just as for true T_1.

For c=7, the forward-invariant set B_7={n>0: 7 does not divide n} has natural density 6/7 and does not meet the cycle 7<->14. The second genuine positive cycle is 5->11->20->10->5. Since 7|T_7(n) iff 7|n, invariance is elementary.

For every h and each parity word w of length h, among n=1,..,7*2^h there are EXACTLY SIX members of B_7 with parity word w. Proof: the parity word selects one residue mod 2^h, and the Chinese remainder theorem supplies exactly 7 different residues mod7, six of which are not 0. This is full conditional finite-horizon parity uniformity WITH a permanent bad sector. Local finite audit checked h=1..9.

=> Any route relying only on uniform finite parity suffixes, even CONDITIONED on a bad sector, is rejected.

## 4. Stronger negative control: high-odd nonterminal cycle and rational lattice

For c=5, the positive integer cycle beginning at 187 has exactly 27 shortcut clocks, 17 odd; minimum 187. The independent exact affine cycle audit yields

    D = 2^27 - 3^17 = 5,077,565
    B = 189,900,931
    D*187 = 5*B

Dividing every cycle state by 5 gives a **positive rational periodic orbit for the EXACT +1 shortcut formula**, using parity of the numerator on rationals with odd denominator. The start is x=187/5, a non-integer. Its odd fraction 17/27 is about 0.629630 and its required minimum-step fraction log(2)/log(3+5/187) is about 0.625875. The high-odd regime does NOT alone exclude periodicity. What distinguishes genuine natural-source Collatz is the denominator-one condition.

Other T_5 positive cycles rooted at 19, 23, and 347 coexist in the same nonmultiple-of-5 sector, so absence of a simple gcd barrier within a sector does not alone force basin uniqueness. The 187 cycle is previously known in generalized Collatz literature; do NOT claim historical priority for its discovery.

## 5. Negative control: no fixed-modulus pointwise dual contraction

For EVERY fixed modulus M>=1 and q>=1, set

    y=3*M*q-1, p=2*M*q-1.

Then 0<p<y, both p and y are -1 mod M, p is odd, and T_1(p)=y. If w(n)=f(n mod M)/n^s for any s>0 and any positive fixed periodic f, then w(p)>w(y).

So a sourcewise inequality sum_{T(n)=y} w(n) <= lambda*w(y) with lambda<=1 CANNOT hold for all sufficiently large y. This is an exact infinite family. It rules out the SIMPLE fixed-residue positive dual witness, not shell-averaged estimates, source-dependent weights, or hypothetical bad-set-conditioned estimates. The adverse self-loop is a finite-modulus shadow of the unbounded Mersenne/odd corridor.

## 6. Status and next smallest decisive experiment

- WARRANTED inherited: V165 unconditional source-product class conservation; V167 finite source-ordered proof reuse and fixed-H rank no-go.
- EXACT LOCAL / ELEMENTARY: guard-complete one-clock weighted renewal, T_7 conditional mixing countermodel, T_5 27-cycle rational shadow, finite-modulus pointwise dual no-go.
- UNKNOWN: any TRUE +1 all-scale source-height dependent strict replenishment deficit; any bound excluding the required ~35.19% s-weighted bad-class ternary bias.
- REJECTED: finite conditional parity mixing alone; raw two-clock merger count as terminal proof; c-independent drift / rational-positive growth; all-target finite-modulus pointwise dual contraction.
- Smallest experiment: add **exact height-boundary export and per-clock terminal-admission gain** to the V166 proof compiler, keeping original source, clock, and already-certified smaller-target lineage. Numerically examine the near-critical y=2 mod3 weighted reservoir, but promote only an exact all-height arithmetic inequality from true +1 integrality; run c=5 and c=7 controls. Deriving R_s(B)<=1/3 from mere class invariance is circular. The target must emerge from a separate source-height theorem.

**NO QED. This checkpoint must not be read as a proof of a positive spectral gap.**


## 7. V168B: exact infinite-source SINGLE fixed-block contraction, not QED

[Source-pinned green V168B two-job qualification](https://github.com/heathsanchez/test/actions/runs/38085059622), exact head d1d159475c6e77b9e1a83026d36af434252f6908. Independently executed complete integer proof-audit source: [collatz_v168_rigorous_single_block_gain.py](https://github.com/heathsanchez/test/blob/d1d159475c6e77b9e1a83026d36af434252f6908/research/collatz_v168_rigorous_single_block_gain.py). The new result is an unconditional analytical inequality for ALL original positive natural sources but ONLY for clocks 40 and 60. It is NOT a uniform spectral gap, an all-H estimate, or a proof of full Collatz. It is not yet a Lean theorem.

With S(H)=sum_{n>=1} U_H(n)/n^(3/2), where U_H(n) is exact *terminal*-timeout by real shortcut clock H, define X=2^18 and Q=10^12.

A source-by-source EXACT computational audit for EVERY 1<=n<X finds:
- U_40(n)=1 for 229,259 sources;
- U_60(n)=1 for 164,657 sources;
- 64,602 genuinely newly terminal-certified original sources at clocks 41..60 (not just an uncertified earlier-source merger).
Use integer floor b_n=floor(Q/sqrt(n^3))=isqrt(floor(Q^2/n^3)), no floating arithmetic.

Integer witnesses:
- finite S(40) lower weight units: 125,286,327,534;
- finite S(40) UPPER units: 125,286,556,793 (one Q^(-1) slack per timeout);
- new genuine terminal gain LOWER units: 26,452,894,380.
The entire *infinite* unexamined tail obeys sum_{n>=X}n^(-3/2)<=2/sqrt(X-1)<1/250 because X-1=262143>250000. Thus S(40)<129286556793/Q while S(40)-S(60)>=26452894380/Q.

Consequently, with D=129286556793 and G=26452894380:
  S(60)/S(40) <= 1-G/D = 102833662413/129286556793 < 4/5
where the final comparison is exact integer cross-multiplication, and S(40)>0 from any surviving n<X.

**The proof covers ALL n>=1 with exact tail control, but only one finite clock interval.** It exploits real terminal admissions plus an analytic summable weight, not V165's conservation. The same method could certify fixed-clock gains for other systems with multiple basins and cannot be iterated without an independently proved uniform clocked renewal theorem.

**Promotion boundary:** WARRANTED_EXACT_CI_PLUS_ELEMENTARY_ANALYTIC_BOUND, NOT yet FORMAL_LEAN. Future work: strengthen to a true Collatz-specific *all-H*, source-height conditioned gain. Every fixed-H gain is compatible with a persistent bad class, so it cannot replace that missing theorem. See CI artifacts for the audit and seal.
