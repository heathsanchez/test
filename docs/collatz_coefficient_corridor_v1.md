# Coefficient corridor V1 — actual-value packing, not global closure

Parent: canonical V12 at `cb65e7143aded6744f464da00fe98f9dd64af488`.
Global Collatz: **UNKNOWN**. The V11 bounded canonical M-negativity result is unchanged.

## Readjustment and exact object

V12 ruled out a translation-uniform, phase-blind Fourier majorant as a way of obtaining a subunit fixed-origin count. This cycle instead uses actual positive orbit values, their distinctness, and their lower bound by the original source. It does not claim an origin anti-concentration theorem.

For the shortcut map T, put x_i=T^i(n), q_i equal to the odd count before time i, and rho_i=3^q_i/2^i. Define the positive correction product

    P_j = product over odd x_i, i<j, of (1+1/(3*x_i)).

The exact multiplicative identity is

    x_j = n * rho_j * P_j.                                      (1)

This follows by multiplying the one-step ratios; it is standard Collatz algebra, not a claimed new discovery. The same product is used in Rozier–Terracol, Proposition 4.1, https://arxiv.org/html/2502.00948v5. The newly recorded item here is the shifted sixth-power packing certificate and its explicit fixed-corridor application. No literature-priority claim is made.

## 1. Exact one-factor inequality

For x>1,

    (1+1/(3*x))^6 < (x+1)/(x-1).                               (2)

After clearing positive denominators, the difference is exactly

    (3*x)^6*(x+1) - (3*x+1)^6*(x-1)
      = 243*x^5 + 675*x^4 + 405*x^3 + 117*x^2 + 17*x + 1 > 0.

More generally, if x>=a>1, then

    (3*x+1)^6*(a-1) < (3*x)^6*(a+1).                           (3)

The Lean proof avoids division and subtraction by writing a=u+2, x=a+d and proving the polynomial identity

    (3*x)^6*(u+3)
      = (3*x+1)^6*(u+1) + remainder(x) + d*increment(x),

where remainder is the positive polynomial above and

    increment(x)=(3*x+1)^6-(3*x)^6
      =1458*x^5+1215*x^4+540*x^3+135*x^2+18*x+1.

Every displayed summand is nonnegative and remainder has constant term one.

## 2. Distinct-odd-value packing

Assume n>=3 is odd. Consider any finite orbit segment whose q>=1 odd terms before its endpoint are distinct and all at least n. Sort these odd values as m_0<...<m_(q-1). Then

    m_r >= n+2*r.

Applying (3) with a=n+2*r and multiplying gives the telescoping estimate

    P_j^6 < product_r (n+2*r+1)/(n+2*r-1)
          = (n+2*q-1)/(n-1).                                  (4)

The bound is phase-sensitive in the relevant sense: it uses the actual lower endpoint n and distinct actual integer values. It is not unchanged by translating the source-residue support. It is not a bound proved solely from word count or Fourier magnitudes.

The Lean theorem `packed_sixth_power` formalizes the product estimate for an arbitrary list satisfying `Packed n xs`, where successive lower bounds increase by two. The conversion of a sorted list of actual distinct odd terms to Packed, the orbit identity (1), and the application below are written mathematics in this cycle, not a new complete Lean orbit theorem.

Distinctness matters. Repeating the odd value 5 ten times gives (16/15)^60>6, contrary to the proposed packed upper bound 6. Such a multiset cannot be treated as ten distinct odd states.

## 3. Fixed coefficient corridors have finite fuel

In addition assume every prefix coefficient up to the segment endpoint is at most an integer C>=1. Because P_i is nondecreasing, (1) implies

    x_i <= C*n*P_j

at every prefix. The largest of the q distinct odd values is at least

    L=n+2*q-2.

Together with (4), this yields the exact necessary inequality

    (n-1)*L^6 < C^6*n^6*(L+1).                                (5)

This has a simple conservative integer consequence:

    q < C^2*n.                                                 (6)

Proof: L>=n>=3, so L+1<=2L. Divide the positive factor L in (5) to obtain

    (n-1)*L^5 < 2*C^6*n^6.

If L>=2*C^2*n, the left side is at least

    32*C^10*n^5*(n-1) >= 16*C^10*n^6 >= 16*C^6*n^6,

using n-1>=n/2 and C>=1, a contradiction. Hence L<2*C^2*n. If q>=C^2*n then L=n+2q-2>=2*C^2*n, another contradiction.

Thus C^2*n-q is a finite odd-step budget while these hypotheses and the SAME C remain valid. Even steps leave q unchanged and cannot continue indefinitely on a positive orbit without an odd step. This is not asserted to be a strict rank on every raw shortcut step.

## 4. Consequence for an infinite never-crossing positive source

Suppose rho_i>=1 for every i for a positive source n.

First, n=1 cannot satisfy this, since its coefficient at depth two is 3/4. An even positive source crosses at depth one. Thus n is odd and n>=3.

Equation (1), or the existing affine identity with positive bias, implies x_i>=n at every prefix.

There can be no repeated orbit value. A repeated value produces an eventually periodic positive orbit. Its period contains an odd step (a cycle of positive halving steps is impossible). Applying (1) around that period shows its coefficient multiplier is the reciprocal of a correction product strictly larger than one, hence is strictly below one. Repeating that period would eventually drive the cumulative coefficient below one, a contradiction.

There are infinitely many odd steps, since otherwise the orbit would eventually consist solely of positive halvings, also impossible. All odd terms are distinct and at least n. If all rho_i were bounded by some finite C, choose an integer C>=1 above that bound. Inequality (6) for all finite prefixes would bound their odd counts, a contradiction.

Therefore the written elementary consequence is

    positive never-crossing orbit => sup_i rho_i = infinity.     (7)

More quantitatively, (5) forces coefficient peaks at least of order q^(5/6), with a source-dependent constant. This is a statement about prefix MAXIMA, not a claim that rho_i tends to infinity or that it cannot return near one.

## 5. Exact failure boundary — no global rank has been obtained

The ceiling C must stay fixed. Replacing it with the current running ceiling replenishes the budget. An actual example is n=3: initially C=1,q=0 gives budget 3; after the first odd step rho=3/2, C=2,q=1 gives budget 11. Thus this proposed globalized budget increases.

A never-crossing orbit could still escape through arbitrarily high coefficient corridors. A near-critical limiting odd density is also not excluded: logarithmically unbounded coefficient surplus can coexist with q_i/i tending to log_3(2). No upper bound on the coefficient peaks has been proved. No conclusion about every finite first-crossing terminal with M>=0 at unbounded depth follows from this lemma.

This is not a revival of a finite residue SCC proof, a bounded-valuation periodicity assertion, or the rejected coarse p-adic tracking argument. The hypotheses are explicit real coefficient bounds and actual distinct integer values; the reasoning is exact algebra and packing.

## 6. Reproducibility and verification

Run `python -S experiments/collatz_coefficient_corridor_v1.py`.

The exact probe covers all 4,095 odd sources 3<=n<8192 and checks 20,266 coefficient-live prefixes. It independently multiplies the actual correction factors, compares with (1), and checks (4), (5), and (6) using rational/integer arithmetic. There are no failed comparisons. The independently expanded polynomial difference has coefficients [1,17,117,405,675,243,0,0]. The unchanged trace digest is `4374309f594e41806701cd7a2ddd7a60f376263664258452785c284b838d0d2e`.

The Lean gate separately compiles `formal/Collatz/CoefficientCorridor.lean` on the existing pinned core toolchain and prints dependencies for the polynomial identity, one-factor majorant, and arbitrary-length packing estimate. Qualification is recorded only after that gate completes.

Declared boundary: the finite probe does not prove the all-depth theorem; the written argument does. Lean checks the generic packing algebra, not the complete orbit/sorting/periodicity application. The V11 large finite certificate is inherited, not rerun or extended. The global Collatz status remains UNKNOWN.
