# Collatz V184–V185 — source-specific protected-future repair

**11 October 2026 NZ. WARRANTY: formally checked necessary all-prefix odd condition + original-source-specific coefficient guard + certified coefficient-excess-to-earlier-source constructor. GLOBAL COLLATZ UNKNOWN — NO QED.**

## Source-pinned evidence

- [V184 full green CI #38102257750](https://github.com/heathsanchez/test/actions/runs/38102257750), exact commit 698524d4c6a4dca50e9cee3d3ae4770409427a8f. [Formal module](https://github.com/heathsanchez/test/blob/698524d4c6a4dca50e9cee3d3ae4770409427a8f/formal/Collatz/PersistentOddPrefixBarrier.lean) and independent [exact audited controls](https://github.com/heathsanchez/test/blob/698524d4c6a4dca50e9cee3d3ae4770409427a8f/research/collatz_v184_persistent_odd_audit.py).
- [V185 full green CI #38102703359](https://github.com/heathsanchez/test/actions/runs/38102703359), exact commit b10978d5a5b1e64183362a0b5572b10cc7de52cc, branch [collatz-v185-source-specific-future-guard](https://github.com/heathsanchez/test/tree/collatz-v185-source-specific-future-guard), [formal module](https://github.com/heathsanchez/test/blob/b10978d5a5b1e64183362a0b5572b10cc7de52cc/formal/Collatz/SourceSpecificFutureGuard.lean) and [exact source/clock audit](https://github.com/heathsanchez/test/blob/b10978d5a5b1e64183362a0b5572b10cc7de52cc/research/collatz_v185_source_exact_audit.py). Three independently qualified jobs on the exact source commit, foundational Lean axioms only and no sorryAx.

## Metalogic encounter → residual → minimum repair → warrant

**Protected future.** A hypothetical least positive bad source n has the previously kernel-checked all-clock invariant T^t(n)>=n for EVERY t. That is a future property, not merely source height or an empirical first-horizon timeout.

**Old coarsening.** V181's high-odd condition required a clock-dependent height bound n>=2^(10r), applying at only finitely many r for a fixed source. V184 used the protected all-clock never-below-original-source property to prove an unconditional necessary condition for any least bad n>=8:

  oddCount(n,5r)>=3r+1 FOR ALL r>0.

At every source clock k, a true orbit with all earlier states >=8 satisfies

  2^k*8^oddCount(n,k)*T^k(n) <= n*25^oddCount(n,k).

**Adverse witness.** Genuine non-Collatz generalized T5(odd n)=(3n+5)/2 has a 27-clock 187-minimum cycle with 17 odd steps. It satisfies this coarse 3/5 necessary restriction indefinitely. The finite n>=8 multiplier merges true +1 and this false model, and therefore is NOT a sufficient invariant.

**Least lawful change.** Retain original source n and exact +1 odd intercept at every clock. If x>=n is odd under TRUE T,

  2*n*T(x) = n*(3*x+1) <= (3*n+1)*x.

The new Lean source-exact prefix theorem is

  IF n<=T^t(n) FOR ALL t<=k,
  THEN 2^k*n^a*T^k(n) <= n*(3*n+1)^a,
       2^k*n^a <= (3*n+1)^a,
       a=oddCount(n,k).

Unlike V184 this requires no coarse n>=8 condition; for a least positive bad n it holds at ALL k because of protected minimality.

**Exact negative separator.** On the G5 187-cycle signature (k,a)=(27,17), the prior coarse inequality 2^27*8^17<=25^17 holds, but the exact TRUE +1 inequality 2^27*187^17<=(3*187+1)^17 FAILS. Lean verifies the strict opposite as pure source arithmetic, and the independent program verifies the actual G5 cycle. G5 is not the true +1 map, so this is NOT a counterexample to Collatz.

**Compiled practical consequence.** V185's two new kernel-qualified theorems establish

  IF (3*n+1)^a < 2^k*n^a
  THEN EXISTS real clock t<=k and REAL source p=T^t(n)
       with 0<p<n and genuine two-clock future meeting T^t(n)=T^0(p).

The certificate is one-way: the source/clock/odd count suffices to guarantee a smaller genuine future source when the strict inequality holds. Equal odd count by itself does NOT certify full future equivalence, and should not lead to an unsound global quotient.

**Reclose.** V185 also kernel-checks the conditional strong-induction theorem: IF every n>1 eventually produces that exact coefficient-excess witness, THEN every positive n converges. The genuine 1↔2 terminal source1 is explicitly excluded as the lawful induction base. This is a conditional logical bridge, not QED.

## Remaining irreducible gap

The event-production premise remains unproved:

  For each positive n>1, find some genuine k such that
  (3*n+1)^oddCount(n,k) < 2^k*n^oddCount(n,k).

Requiring that premise for all n>1 is a reformulation at least as difficult as Collatz, not an independent advancement in its truth. The earlier V168 proposed terminal-disconnected-class weighted residue share upper bound, including 0.35, remains unproved. The V170/V171 sparse no-two-macroscopic-component estimate remains unproved; its external timed target-predecessor density input still needs cold local verification.

**Decision:** Source-dependent +1 exactness is now a verified minimal, testable distinction; the artificial G5 counterworld is separated without expanding to another search oracle. The future source-independent event-production or invariant-class anti-replenishment theorem remains the actual open problem. UNKNOWN — NO QED.
