# Collatz source-floor gap V1

Date: 2026-09-26. Parent state: `3ae1c9023b7883977132655ba771c9239828b9b0` (V9). Global status: **UNKNOWN**.

Qualified implementation: `d1c8c36d016fa444e613a0b3553c8948d8790a65`. Hosted source-floor run **36224119410**, job **108354738591**, SUCCESS. Artifact **10899609146**, SHA-256 `79c5b0aaca9c4df4662bab47965e567de5e913775249141caa7ceda99f1f4ff2`. The existing source-product qualification also passed at this head, run **36224119443**.

## Objective and unchanged canonical residual

Exclude every nontrivial legal first-coefficient-crossing cylinder with canonical margin `M=B-(2^j-3^q)R>=0`. V9 additionally exposed the global crossing-existence obligation and proposed a live-origin bound. This cycle does not conflate that terminal-cylinder problem with global convergence.

Two sequential questions were tested: does P37 admit a depth or source-window rank; and can existing source-range authority replace V9's proposed new finite enumeration through its analytic cutoff?

## 1. Elementary all-depth bias bound

Write `A=2^j`, `P=3^q`, `D=A-P`, and `A*T^j(n)=P*n+B`. Suppose no coefficient crossing occurs before depth j. At an odd step with index i and q_i preceding odd steps, the increment of `B/P` is `2^i/3^(q_i+1)`. Since `2^i<=3^q_i` at every earlier prefix, this increment is at most 1/3. Summing the q contributions gives

    3 B <= q 3^q.                                      (1)

This uses actual source-orbit semantics, not a proposed abstract source language. It is weaker than some archived extremal bounds but entirely elementary.

If the j-th endpoint is nondescending and D>0, the exact affine identity implies `D*n<=B`. Hence

    n <= floor(q*3^(q-1)/(2^j-3^q))                    (2)

for q>0. The case q=0 has B=0 and cannot be a positive nondescending crossing.

The Lean file `formal/Collatz/FirstCrossingBias.lean` proves (1), the necessary first-crossing coefficient-type lower bound, and the exact source-floor interface. Its hypotheses include earlier-prefix legality, actual non-descent, and a stated integer cap comparison. It does not assert crossing existence or any external convergence result.

The three theorems are `elementary_bias_bound_of_no_earlier_crossing`, `first_crossing_type_lower`, and `source_lt_floor_of_first_crossing_cap`, all in `CollatzFinal.SourceProduct`. The successful gate printed only `propext` and `Quot.sound` for their dependencies; no `sorryAx` or `Lean.ofReduceBool` was admitted.

## 2. Complete exact coefficient-type coverage through 271782

Any first crossing satisfies `2^(j-1)<=3^q<2^j`, so `j=bit_length(3^q)`. This gives two independent exhaustive enumerations: increment j while maintaining the adjacent power of 3, or increment q and read the bit length of 3^q.

Python uses the first enumeration, C++/Boost the second. Both independently check the integer cap (2). They agree on:

- Depth range: 1 through 271782, inclusive.
- Necessary first-crossing coefficient types: 171476, including the q=0,j=1 base type.
- Largest source cap: **7,216,089,270**.
- Maximizing type: **j=125743, q=79335**.
- Convenient encompassing source floor: **2^33=8,589,934,592**.

The SHA-256 of all depth-indexed `j,q,cap` rows is `8216be5be97304bc66f6ae6b5f94c04ed93b083768cf0ea4140642b840dfb663`. The finite report also retains all 36 record caps. No floating logarithms or powers are used for these decisions.

An independent canonical source-product enumeration through depth 18 checks the affine identity and elementary bias inequality on 18,492 symbolic nodes.

### Correct consequence and its boundary

Within the declared Lean-plus-exact-checker boundary: any actual nondescending first crossing at depth at most 271782 starts below 2^33. The symbolic bridge is Lean-checked; the large finite enumeration is independently replayed Python/C++, not a Lean proof term.

Conditional on verified convergence below 2^33: no minimal Collatz counterexample can have such a first crossing. This fills the finite **minimal-counterexample** gap needed by V9 when its live-origin estimate starts no later than this cutoff.

It does **not**, merely from a convergence floor, prove that every first-crossing cylinder in the finite interval has M<0. A convergent source could hypothetically fail to descend at its first coefficient crossing and descend later. The stronger canonical cylinder target is retained separately.

The requisite source-range result is contained in Barina's published verification below 2^71. We checked the primary paper/project statement, not the underlying full computation:

- David Barina, *Improved verification limit for the convergence of the Collatz conjecture*, Journal of Supercomputing 81, 810 (2025), DOI 10.1007/s11227-025-07337-0.
- https://link.springer.com/article/10.1007/s11227-025-07337-0
- https://pcbarina.fit.vut.cz/

This is an explicit external computation boundary. No interval extension of the previously rejected Ansari type is used.

The August ledger P11/P17 already contains the source-floor direction and a stronger conditional Farey denominator floor. This cycle is not a claim to invent that idea. It supplies a smaller direct certificate for the cutoff actually needed here, without relying on the archived harmonic/Farey certificate.

## 3. P16 is unnecessary for this polynomial-window reduction

Let `Lambda=j log 2-q log 3>0`. From (1),

    n <= q/[3(exp(Lambda)-1)] < q/(3 Lambda).

Using the declared Rhin lower bound `Lambda>=j^(-13.3)` for j>=2 gives

    n < (q/3) j^13.3 <= (1/3) j^14.3 < j^15.        (3)

Thus the same live-parent window `X_(j-1)=j^15` works without P14/P16, Denjoy-Koksma, source-tail elimination, or P36. Those archived results are not invalidated; this particular implication no longer needs them.

The external logarithmic bound is stated as Proposition 6.3 in Rozier and Terracol, *Paradoxical behavior in Collatz sequences*, arXiv:2502.00948v5, citing Rhin (1987):
https://arxiv.org/html/2502.00948v5#S6

That published statement was checked. Rhin's original computer-assisted proof and the real-analytic deduction (3) are not newly Lean-formalized in this cycle.

## 4. Exact P35 lattice improvement, followed by decisive P37 obstructions

P35 previously used strict improvement `M>M0` to infer `R<=floor((Bstar-M0-1)/D)`. Since all same-type margins lie in `2^j Z`, strict improvement actually implies `M>=M0+2^j`. Therefore the stronger exact window is

    R <= floor((Bstar-M0-2^j)/D).                    (4)

This is an integer-lattice consequence, not a fitted constant or an attempt to reactivate the rejected reverse-grammar gap-tightening route. It concerns strict beaters, not all ties. For proving strict negativity directly, the same lattice says M<0 iff M<=-2^j; zero-margin candidates must not be discarded.

The increasing source scan below 2^20 finds exact minimum-source incumbents for 104 observed nontrivial types. Types absent from that scan are not claimed covered. Reusing P14's critical mechanical Bstar formula, the strict-beater windows contain 4174 extra odd candidates before (4) and 3785 after it. There are 1918 trivial-type exits, one direct same-type comparison, and 1866 distinct-type dependencies.

**Depth rank is false.** For parent type j=111, incumbent 45055 maps to 43444. Its old cap is 45434 and lattice cap is 45406. The extra candidate 45127 is in both windows, but its first coefficient crossing is at **129**, ending at 29405. Thus a P37 candidate can map to a greater crossing depth. It is not a hypothetical M>=0 counterexample; it is a counterexample to the proposed rank on competitor-type recursion.

**The lattice-cap rank is also false.** Type 40 maps via candidate 159 to type 21 with equal caps 160. More decisively, type 54 maps via candidate 103 to type 42, while the lattice cap grows **103 -> 105**.

These reject the two specified rankings, not P37 itself. No tuned linear combination of depth and cap is promoted. The j=54 same-type candidate is compared by exact margin, not misrecorded as a recurrent self-loop.

## 5. Precise remaining global obligation

Retain V9's live set A_j, its size F_j, and its live-origin count P_j(X). A coverage-complete candidate is

    P_j((j+1)^15) <= 2*2^(6j/125)*F_j*(j+1)^15/2^j

for every j>=271782, or with another explicit onset whose finite preceding interval is separately covered.

V9's exact entropy/cutoff argument would then give empty live windows. Cofinality excludes never-crossing positive sources; (3) excludes late nondescending first crossings by injecting their sources into empty live parents. The new finite source-cap certificate and a declared convergence floor exclude early minimal-counterexample crossings. This would yield a global minimal-counterexample contradiction, not merely finite language sparsity.

**The live-origin inequality is still UNKNOWN.** An unspecified eventual onset is not assumed below the scanned cutoff. The all-depth canonical M-cylinder target and any universal P37 residual-preserving rank also remain UNKNOWN.

## Verification and reproducibility

Run from the repository root:

    python -S experiments/collatz_source_floor_gap_v1.py
    g++ -O2 -std=c++17 experiments/collatz_source_floor_gap_v1.cpp -o /tmp/cap-check
    /tmp/cap-check

The hosted workflow `.github/workflows/collatz-source-floor-gap-v1.yml` compares the complete Python output with the committed report, independently compares C++ results, explicitly compiles the imported Lean source-product modules and the new bias file, and checks printed axiom dependencies. It also explicitly checks the previously ungated first-crossing uniqueness module.

Failed qualification lineage is retained: run 36223928027 at ea18488b failed because the runner lacked Boost headers; run 36223997463 at b2a309d6 passed numerical checks but exposed Std-only proof-rendering omissions. Neither is authority for the Lean theorem. Run 36224119410 at d1c8c36d is the complete successful gate. First-crossing uniqueness is now also checked, with the same standard axiom boundary.

Global Collatz remains **UNKNOWN**.
