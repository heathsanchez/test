# V169 — clocked predecessor density versus the largest unseeded future component

**11 October 2026 NZ — CONDITIONAL FORMAL BRIDGE / EXACT BOUNDED TESTS. GLOBAL COLLATZ UNKNOWN.**

This work reconciles independently qualified V165 (future-class mass conservation), V167 (source-ordered terminal proof reuse), V168-retroactive (arbitrary authentic two-clock graph receipts) and V168-weighted (genuine terminal mass renewal). It does NOT supersede any of their bounded or negative findings.

## Objective and exact external premise

For positive source cutoff X_k=2^k and clock H_k=8k, form a finite graph of all original positive n<X_k whose edges carry certified equal true shortcut endpoints at two **real, independent clocks no greater than H_k**, together with independently verified terminal seeds {1,2}. Let M_k be the largest number of original sources in any component not linked to a terminal seed.

**CANDIDATE arithmetic theorem**: M_k/2^k -> 0. This is not proved. It allows isolated timeouts and small disconnected components at every k; it is weaker than the condition that *all* unknown mass tends to zero, since many small disconnected components can coexist.

External premise: Idris Ali Shaik, Positive Density of Collatz Convergence at Every Rate Above 3/log(4/3), 2026-09-21, [paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7497758) and [public Lean source](https://github.com/shaikidris/CollatzConvergencePositiveDensity/blob/main/Solution.lean), declaration `CollatzWordCert.collatz_hitting_positive_lower_density`. It states targetwise positive lower natural density for positive targets not divisible by 3, hitting them within any c log n **ORDINARY** clocks for every c>3/log(4/3). **The theorem's complete foreign Lean dependencies have not been rebuilt/imported in MathGraph; local authority remains explicitly external.** It is not itself a Collatz convergence theorem.

## Precise conditional route to QED (not a claimed result)

1. Assume a bad positive natural source. Take its least positive member m. It cannot be even, as T(m)=m/2<m; it cannot be 1 mod 4, since for m=4q+1 with q>=1, T^2(m)=3q+1<m. Thus m=4q+3.
2. Let a=T(m)=6q+5. Then a is odd, a>0, not divisible by three, and bad (if a reached {1,2}, so would m). The explicit odd target avoids a critical ordinary-to-shortcut **phase** error: ordinary C(odd x)=3x+1 can be an even intermediate skipped by shortcut, but an ODD target cannot be skipped. Any ordinary hit of this a within t clocks gives a genuine shortcut hit within <=t clocks.
3. Set c=11. Numerical arithmetic gives 3/log(4/3)≈10.42818<11 and 11 log 2≈7.62462<8. For each source n<X_k, a real ordinary hit within c log n has a true shortcut hit within H_k=8k clocks.
4. The Shaik premise supplies some delta_a>0 and k0 such that for all k>=k0, at least delta_a*2^k/2 DISTINCT original sources n<X_k hit a in that budget. (The precise constant may depend on a; its value is not required.)
5. Every such n is **in the same true future class** as a, and cannot belong to a terminal-seeded component. In a COMPLETE H_k source-locked endpoint graph, each n has a witnessed edge from T^i(n)=a=T^0(a), hence the graph component containing a must contain at least delta_a*2^k/2 sources.
6. Therefore a verified M_k/2^k->0 theorem would contradict the bad target and prove universal Collatz convergence.

IMPORTANT: **This is a conditional QED bridge, NOT QED.** Its missing true arithmetic is an all-scale bound on M_k. The external target-hitting theorem must be correctly translated and independently imported/reverified before any all-formal result.

## Formal work and its exact boundary

The [new core-Lean source](../formal/Collatz/ClockedGiantComponentBridge.lean) imports existing retroactive soundness and formally checks:
- source-attached finite-clock hitting implies genuine two-clock future meeting;
- if a target is genuinely bad, every true clocked ancestor is genuinely bad;
- no checked future-edge path into a genuinely bad target can be terminal seeded;
- a FINITE LIST of genuine clocked predecessors, provided each is connected by verified ledger paths, lies entirely in a single terminal-disconnected component.

The theorem is deliberately a source-membership inclusion statement rather than a new source-count bound. Finite cardinal consequences require source distinctness and graph completeness; the external positive-density input, all-scale M_k bound and effective clock converter are NOT discharged in this Lean file.

The CI gate checks the exact named Lean statements and limits axioms to standard logical foundations. Earlier CI predecessor failed due to an unavailable Mathlib module and was corrected using the repository's existing Lean core. No Mathlib imported.

## Exact bounded computational falsification

Reuse **unchanged** V168 C++ source/true clock graph compiler, setting `ownerMaxClock=initial_H=8k`; no adaptive late owner steps. Independently recompute small k=8,10,12 in Python by fully scanning all clock endpoints (without C++'s good-class early-stop optimization).

Results:
- True T1: k=8,10,12,14,16,18: 0 unseeded components.
- True T1: k=20,H160: TWO unresolved singleton components; initial isolated original positive sources include 1,027,431 and 1,042,431. They are NOT nonconvergence examples. True actual terminal clocks separately replayed at 238 and 276.
- True T1: k=22,H176: FIVE unresolved original sources in THREE components, largest component contains TWO.
- True T1: k=20,H184: all bounded original sources connected to certified terminal component (zero unseeded), a finite 184-clock graph result, NOT a universal height law.
- Synthetic G7: k20,H160: 898,779 unresolved original sources, one giant terminal-disconnected component greater than 898,000 (approximately 85.7% of the cutoff). G7 genuinely has a distinct nonterminal-to-{7,14} positive cycle {5,11,20,10}. Thus the compiler does NOT promote generic coalescence to terminal convergence.

The k20 H160 true singleton exceptions falsify the guessed stronger claim “zero unseeded components at all finite scales with H=8k.” The actual maximal component ratio is tiny in all tested true windows, but no bound uniform in k is claimed.

## Next cheapest decisive arithmetic experiment

Look for a **genuine Collatz-specific anti-giant lemma** that operates on source-height boundary flow, rather than on generic parity mixing or unsound finite modulus connectivity. Build the smallest exact (+1)-specific inequality that forces M_k/2^k small, and test it against the giant G7 component and high-odd c=5 cycles, including V168-weighted residue2 replenishment.

Any proposed contraction that also holds for G7 or c=5 cannot eliminate distinct basins; any estimate that only holds empirically through k=22 remains CANDIDATE. Report first adverse source/height family when an inequality fails.

**STATUS: conditional formal membership warranted only upon successful CI, bounded finite graph audit qualified upon successful exact CI; asymptotic anti-giant M_k/2^k->0 UNKNOWN; external theorem locally unbuilt; GLOBAL COLLATZ UNKNOWN.**
