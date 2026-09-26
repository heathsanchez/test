# Collatz live-origin bridge V1 — coverage-complete conditional synthesis

Date: 2026-09-26. Global Collatz status: **UNKNOWN**.

## Provenance and authority

Causal parent: `heathsanchez/test:collatz-universal-source-product-v1@7ef09fc8080d15fdb5c211e3e716518ea3cc1431`, hosted origin-finish implication run `36219836579` SUCCESS.

This cycle retains the canonical residual: exclude every nontrivial legal first-coefficient-crossing cylinder with canonical joint margin `M >= 0`. It does not replace it with a finite quotient, static source admission, or a rung-specific residual.

The uploaded `Collatz_Research_Dossier.md` consolidates an older mixed archive. Its actual-step classifier v135.3 remains REPORTED within that archive, while its central coverage/macro-rank obligation remains relevant. The current source-product development supplies actual-orbit representation, exact affine coupling, and a crossing-conditional margin bridge; it does not establish that every source has a coefficient crossing.

Primary live source:
- `formal/Collatz/SourceProductAffine.lean`: exact affine identity and `canonical_margin_nonnegative_of_nondescending`; the latter explicitly assumes `hcross`.
- `formal/Collatz/FinalKernel.lean`: generic strict-descent and well-founded-rank wrappers, not a completed instantiated global rank.
- August ledger P35: exact strict-beater source window; P36: reported/certified finite margin coverage through depth 447; P37: finite residual-depth recursion signal, not universal induction.

No external theorem is newly verified here. P16/Rhin and the archived finite margin certificates retain their existing declared verification boundaries.

## 1. The missing join: exits and survivors are different objects

Use the shortcut map T(n)=n/2 for even n and (3n+1)/2 for odd n. Let q_j count odd steps through depth j.

A coefficient crossing occurs when 3^q_j < 2^j.

Let L_j be parity words whose FIRST crossing is at j. Let A_j be parity words with NO crossing at depths 1,...,j. Write F_j=|A_j|.

For canonical source residue R(w) in [0,2^j), define

    C_j(X) = #{w in L_j : 0 < R(w) < X}
    P_j(X) = #{w in A_j : 0 < R(w) < X}.

The total word counts satisfy, exactly,

    F_j + |L_j| = 2 F_(j-1).

More importantly, for j>=2 and 0<X<=2^(j-1),

    P_(j-1)(X) = P_j(X) + C_j(X).                  (1)

Proof: a positive integer source below X has a unique source-prefix child without a new high source bit. A live parent either remains live or crosses at the next step; these cases are disjoint and exhaustive. Conversely every child counted on the right has that parent. This also gives C_j(X)<=P_(j-1)(X).

Consequently, an upper bound on terminal counts C_j(X) does not, by itself, show that surviving counts P_j(X) vanish. The terminal family is prefix-free, and a never-crossing path contributes to no terminal count. The previous terminal-origin estimate is therefore not, on its own, a complete proof of global descent unless a separate crossing-existence theorem is supplied.

This is a coverage audit, not a counterexample to Collatz or to the terminal estimate.

## 2. One stronger origin theorem covers both missing cases

Take X_j=(j+1)^15. The sufficient candidate hypothesis is

    P_j(X_j) <= K * 2^(eta*j) * F_j * X_j / 2^j    (2)

for all sufficiently large j, with fixed K and eta below the live-language entropy loss.

Only this cofinal polynomial window is required. A bound for all intervals or all X is unnecessary. However, (2) is a NEW hypothesis on live prefixes; it has not been derived from the terminal-origin hypothesis.

### A. Excluding never-crossing positive sources

Suppose P_j(X_j)=0 for all j>=N and X_j<2^j in that range. If a fixed positive integer n never crossed, choose j>=N with n<X_j. Its canonical source residue is then n, so its live prefix is counted by P_j(X_j), contradiction.

Thus eventual live-window emptiness proves that every positive source has a finite coefficient crossing.

### B. Excluding late nondescending first crossings

The exact affine identity at a crossing is

    2^j T^j(n) = 3^q n + B,  D=2^j-3^q>0.

Non-descent T^j(n)>=n implies D*n<=B directly. Under the existing declared P16/Rhin bounds,

    B <= 2^j*j/4,
    D > 2^j/(3*j^13.3),

hence

    n < U(j) := (3/4)*j^14.3 < j^15 = X_(j-1).

No new zero-tail or source-admission argument is needed for this implication; it follows from the same full affine source coupling already represented in Lean.

For a first crossing at j>=N+1, the source's prefix of length j-1 is live. Since n<X_(j-1)<2^(j-1), it would be counted in the empty parent window P_(j-1)(X_(j-1)), contradiction.

This excludes late actual nondescending crossings. The corresponding canonical terminal M>=0 cylinders are likewise excluded by their low-residue live parents under the archived polynomial cap.

### C. Finite closure and descent

One still needs exact nontrivial terminal M<0 coverage for every feasible j<=N, plus the verification of the number-theoretic bounds used above. The archived coverage through 447 is NOT coverage through a larger analytic cutoff.

Then every n>1 has a finite first crossing and descends there. Strong induction on the positive source n gives termination. This is the appropriate place for the existing generic `reaches_one_of_strict_descent` theorem.

The archive's macro-rank and the current origin route therefore fit together: prove finite macro-exits exist, prove each nonterminal macro-exit decreases the source, and use the source itself as the well-founded macro-rank.

## 3. Exact rational entropy and a conditional integer cutoff

This cycle avoids relying on floating-point entropy estimates for its implication certificate.

The exact inequality 3^63 < 2^100 implies every live word of positive length j has q > 63j/100. Taking t=17/10 in the weighted binomial sum gives

    F_j < (27/10)^j * (17/10)^(-63j/100)
        < 2^(951j/1000).

The last strict bound is certified by the exact integer comparison

    27^1000 < 2^951 * 17^630 * 10^370.

If (2) is proved with K=2 and eta=6/125=48/1000, it follows that

    P_j((j+1)^15) < 2*(j+1)^15*2^(-j/1000).

The right-hand side is below 1 starting at j=271782. The equivalent exact test is

    2^271782 > 2^1000 * 271783^15000.

The preceding integer fails that test. The inequality persists thereafter: for j+1>=30000,

    ((j+2)/(j+1))^15000 < 2,

by the binomial expansion bounded by a geometric series. Thus 2^j/(j+1)^15000 increases.

If J0 is the proved onset of (2), use N=max(J0,271782). This is a conservative conditional cutoff, NOT an achieved coverage range. Different proved constants could give a different cutoff.

## 4. Cheapest decisive probe, completed locally

Run:

    python experiments/collatz_live_origin_bridge_v1.py

Exact computation scanned all 524,288 odd sources below 2^20, with coefficient-depth limit 512.

- No unresolved source in this finite scan.
- Largest observed first crossing: 183; first source attaining it: 1,027,431.
- No nontrivial nondescending terminal in this finite scan.
- 635 nonempty live-origin windows at j>=60.
- Zero violations of

      P_j(2^m)*2^(j-m) <= F_j*2^(1+floor(6j/125)).

An independent canonical source-product enumeration through depth 18 examined 18,492 symbolic nodes and matched 342 origin-window checks against the actual-source scanner. Another 10,030 source-window conservation checks passed.

Worst observed normalized live distortion was approximately 0.01720854544 at j=77, m=11, count=4, F_j=117803312204219363447. This logarithmic diagnostic is NOT used for verification; all envelope decisions use integer comparisons.

The tested windows have m<=20 and j<=512. They are not the unbounded polynomial windows required by (2). This is a finite feasibility result, not a universal mixing theorem. The previous separate 2^30 terminal probe was not rerun or silently merged in this cycle.

The independent symbolic checks support the implementation. Identity (1) and the conditional implications above are elementary mathematical arguments; they have not been newly formalized in Lean.

## 5. Stateful research disposition

WARRANTED elementary: source-window conservation, parent injection, the conditional two-case coverage argument, and the rational entropy upper bound.

WARRANTED finite computation: the precisely bounded probe and integer cutoff comparisons reported above.

CANDIDATE: the all-depth live-origin bound (2), preferably attacked through the exact inverse-parity carry operator and P35/P37 recursion, retaining joint state where necessary.

UNKNOWN: the all-depth bound, its explicit onset, finite terminal coverage to the resulting cutoff, and the complete independently checked global formalization.

REJECTED routes remain rejected. No claim that finite residue SCCs, 3-adic-only structure, Pareto chains, adjacent exchanges, or a zero-tail restatement proves termination is revived.

The next decisive target is an origin-sensitive bound on the LIVE carry operator, or an exact obstruction to that bound. The canonical M>=0 residual remains intact; this supplement repairs the coverage needed to turn its eventual exclusion into global descent.
