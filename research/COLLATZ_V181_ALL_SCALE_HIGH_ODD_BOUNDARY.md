# Collatz V180–V181: certified high-odd necessary condition and its exact limit

**11 October 2026 (NZ) — WARRANTED UNCONDITIONAL ALL-SOURCE AFFINE BIAS; WARRANTED ALL-SCALE SOURCE-HEIGHT-CONDITIONED HIGH-ODD BARRIER. GLOBAL COLLATZ UNKNOWN — NO QED.**

## Source-pinned verification

- V180 [three-job GitHub Actions SUCCESS #38100294174](https://github.com/heathsanchez/test/actions/runs/38100294174), exact commit [3f586cf43724129e839dce290804b95b0a49b849](https://github.com/heathsanchez/test/commit/3f586cf43724129e839dce290804b95b0a49b849), [Lean universal affine bias proof](https://github.com/heathsanchez/test/blob/3f586cf43724129e839dce290804b95b0a49b849/formal/Collatz/UniversalAffineBiasOddBarrier.lean), independently checked exact source/clock [V180 audit](https://github.com/heathsanchez/test/blob/3f586cf43724129e839dce290804b95b0a49b849/research/collatz_v180_exact_bias_odd_audit.py).
- V181 [three-job GitHub Actions SUCCESS #38100716247](https://github.com/heathsanchez/test/actions/runs/38100716247), exact [commit 854c6b6a12cc95b267decc5360bc4ce4172563b6](https://github.com/heathsanchez/test/commit/854c6b6a12cc95b267decc5360bc4ce4172563b6), [Lean all-scale high-odd source barrier](https://github.com/heathsanchez/test/blob/854c6b6a12cc95b267decc5360bc4ce4172563b6/formal/Collatz/AllScaleHighOddBarrier.lean), and [exact binomial/Mersenne audit](https://github.com/heathsanchez/test/blob/854c6b6a12cc95b267decc5360bc4ce4172563b6/research/collatz_v181_high_odd_binomial_audit.py).
- Both source-pinned runs checked all named Lean declarations with no sorryAx and permitted standard foundational axioms only, independently audited true shortcut arithmetic, and sealed the exact same source head. The all-m real binomial tail inequality below is an elementary mathematical derivation with exact selected-m checks; it has NOT separately been kernel formalized in Lean.

## A genuine unconditional algebraic theorem, not a random-parity assumption

For T(n)=n/2 if even, (3n+1)/2 if odd, set a=oddCount(n,k), and let B(n,k) be the EXACT nonnegative integer affine intercept already in qualified V160:
  2^k*T^k(n)=3^a*n+B(n,k).

V180 kernel proves for every natural n,k:
  B(n,k)+2^k <= 2^k*3^a.

Thus whenever original source n >= 2^k*3^a and 3^a < 2^k, the real original source descends: T^k(n)<n. There is no source oracle and no claim about an infinite future. The special sharper corollary proves n>=8192 and oddCount(n,12)<=7 imply T^12(n)<n.

The V178 205-rule candidate-position sieve has M=2^12*3^6=2,985,984 exact periodic original-source positions, 2,915,346 excluded from being a hypothetical LEAST bad source, and 70,638 grammar-relative survivors for sources n>=16,384. The independent V180 full-M mask audit proves that EVERY survivor has first-twelve actual oddCount >=8; its exact residue histogram is:
  8: 21,051; 9:29,496; 10:15,735; 11:3,960; 12:396.
None of these 70,638 is proven divergent. The Lean theorem supplies an arithmetic reason for the necessity of an odd-heavy prefix; the exact coverage/odd-signature audit remains separately executable, not 2,985,984 individual Lean propositions.

## V181: an all-positive-clock-scale necessary parity condition

For EVERY m>=1, 27^m<32^m, so 3^(3m)<2^(5m). Combining with the all-source coefficient+intercept bound, Lean proves:
  For all n>=2^(10m), if oddCount(n,5m)<=3m then T^(5m)(n)<n.
  Therefore a hypothetical LEAST positive bad source n>=2^(10m) must satisfy oddCount(n,5m)>=3m+1.

Crucial quantifier: the source-height threshold depends on m. This is a NECESSARY condition for a candidate least bad integer, not a theorem that all large odd-heavy sources descend.

## Exact parity-word upper tail, elementary derivation and prior art

V161 kernel-qualified all-finite-parity-word realization and its independently tested parity-word bijection give precisely binomial(5m,1/2) word counts within complete residue blocks 2^(5m). Let
  A_m = sum_{j=3m+1}^{5m} binom(5m,j).
Among positive source residues whose ACTUAL first 5m steps meet the necessary high-odd condition, the proportion is A_m/2^(5m).

For every integer j>=3m+1,
  3^j * 2^(5m-j) >= 3^(3m) * 2^(2m).
Using the ordinary binomial theorem:
  3^(3m)*2^(2m)*A_m
    <= sum_{j=0}^{5m} binom(5m,j)*3^j*2^(5m-j)
    = 5^(5m).
Consequently
  A_m/2^(5m) <= [5^5/(3^3*2^7)]^m
               = (3125/3456)^m.
The exact Python audit checks this rational integer inequality through m=128, with no floating-point inequality assumptions.

At source-height scale n about 2^(10m), this is an explicit source-position power saving with exponent delta=-log2(3125/3456)/10≈0.0145247. **This is an arithmetic NECESSARY-CANDIDATE density bound, not a bound on the actual bad future-class density.**

**PRIOR ART / NOVELTY GUARD:** natural-density-one finite stopping-time/first-descent phenomena have been known since Terras, *A stopping time problem on the positive integers*, Acta Arithmetica 30 (1976), 241–252 ([EuDML](https://eudml.org/doc/205476)), and independently Everett, *Iteration of the number-theoretic function f(2n)=n, f(2n+1)=3n+2*, Advances in Mathematics 25 (1977), 42–45 ([journal](https://www.sciencedirect.com/science/article/pii/0001870877900871)). The V180–181 result is an independently machine-qualified explicit SOURCE-HEIGHT-CONDITIONED instance integrated into MathGraph's proof semantics, NOT a novel unconditional solution of the stopping-time problem.

## Exact obstruction: infinitely many integers pass the necessary filters

For EVERY m>=1 consider the real POSITIVE original integer n_m=2^(10m+1)-1. For each t<=10m+1 its actual shortcut trajectory begins
  T^t(n_m) = 3^t*2^(10m+1-t)-1.
Hence all of the first 10m+1 steps are odd, including the first 5q for EVERY q<=m. For such q, source height n_m>=2^(10q), and oddCount(n_m,5q)=5q>=3q+1. For q>=m+1 the required height threshold fails: n_m<2^(10q).

Thus n_m satisfies EVERY V181 high-odd necessary condition applicable to its OWN original source height, for all q. The sources n_m are distinct and unbounded. This is a precise first-principles reason the exponentially vanishing candidate density cannot imply an empty candidate set: rarity is NOT impossibility. No nonconvergent true Collatz integer is constructed or claimed.

The independent exact audit replays the Mersenne source/clock identity at m=1,2,4,8,16,32,64,128. An all-m Lean proof of the Mersenne construction itself is not claimed at this checkpoint; its elementary explicit formula is a mathematical observation and separate executable check.

## Research conclusion and next genuine task

WARRANTED: all-source exact intercept control, source-height coefficient crossing descent, infinitely many clock-scale necessary high-odd constraints, finite exact parity word/residual population audits.

REJECTED: the claim that an exponentially small or zero-density set of allowed potential LEAST-bad source positions must be empty. This is false as an inference: source-height thresholds increase with clock depth, and explicit Mersenne integers persist through every applicable high-odd filter.

UNKNOWN: actual convergence of those Mersenne instances at all scales; universal convergence of the whole positive-natural source system; a plus-one-specific ALL-HEIGHT theorem forcing the true bad future-class population to disappear or forbidding two macroscopic disjoint future classes.

**Next decisive distinction:** promote source-attached cross-height meeting/terminal admissions over mere parity-tail restriction. A successful new theorem must use the actual integer +1 successor at every step and rule out PERSISTENT bad future classes, including the odd-heavy Mersenne corridors. Generic finite-word mixing and a finite bank of lower-source progressions cannot do this. Protect G7/G5/S5 and the all-finite-audit hidden-defect negative controls. GLOBAL COLLATZ UNKNOWN — NO QED.
