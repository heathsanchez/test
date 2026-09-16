# Exact return interfaces and frozen compositional transfer

Research checkpoint, 2026-09-16. Parent: ace1fa7a383365fcce11e4ecaccf209d12d3539f.
Status: universal conditional identities with handwritten proofs; independently audited finite experiments. NOT a global Collatz proof or a completed finite recursive closure. No Lean formalization.

## What the supplied ETP paper changes

Heath Sanchez, *The Future-Set Normal Form of the ETP Implication Matrix* (July 5, 2026), separates the preorder identity from empirical compression. For reflexive transitive reachability, A reaches B iff F(B) is contained in F(A). This is forced by transitivity in one direction and B belonging to F(B) in the other. Equal futures imply mutual reachability. Thus a DAG has no nontrivial quotient by raw reachable-node futures: antisymmetry makes equal futures equal nodes. ETP corpus compression numbers are not evidence about Collatz.

Here the useful protected future is instead a language of legal return repetitions. We derive its minimal state, exhibit the continuation it fails to preserve, and retain that information in the executable interface. Following the supplied question/delete/simplify/accelerate/automate methodology, fixed-point class compression is retired where rigidity makes it impossible; cross-pattern injection and exact exit data cannot be deleted.

## Exact domain and transport

Use shortcut T(n)=(3n+1)/2 for odd n and n/2 for even n. Write an odd episode start as n=2^r m-1 with m positive odd. An episode (r,s,r') has r odd shortcut steps, s even steps, and

    m' = (3^r m + 2^s - 1)/2^(s+r').

A nonempty connected same-r return word W composes to F_W(m)=(A m+B)/2^D, where A and B are positive odd. Set C=2^D-A (nonzero odd), and reduce its fixed point B/C=p/u, with u positive odd and p odd.

**Exact domain theorem.** W executes exactly on positive odd m satisfying

    A m+B = 2^D (mod 2^(D+1)),
    equivalently u m-p = 0 (mod 2^(D+1)).

Proof: at the final step, the composed congruence makes the final cofactor odd integral. For a proper prefix (Aj,Bj,Dj) and its nonempty suffix (a,b,d), b is odd and d>=1. Reducing the full congruence modulo 2^(Dj+1) gives a(Aj*m+Bj)+b*2^Dj = 0 modulo 2^(Dj+1). Since a and b are odd, Aj*m+Bj = 2^Dj modulo 2^(Dj+1), forcing that earlier cofactor odd integral. All intermediate rational cofactor values are positive from their formulas. Oddness of m and m' then makes r and s the exact valuations in each episode. The converse follows by composition. Since u is odd, the cylinder contains positive integers. The extra oddness bit cannot be dropped.

For V=(a,b,d) at the same anchor, let Delta_W(m)=Cm-B. Direct substitution gives

    2^d Delta_W(F_V(m)) = a Delta_W(m) + J,
    J = (a-2^d)B + Cb.

J=0 iff the two rational fixed points coincide; this is also exactly the commutation condition for these affine maps. Only on admissible domains does this describe episode execution. When J=0 and the defect is nonzero its 2-adic valuation falls by d. A zero defect is a separate fixed-point case, not a finite countdown.

## Rigidity and the minimal protected language

**Primitive rigidity.** At a fixed anchor r, exact return words with the same rational fixed point are powers of one common primitive episode word.

Proof: WV and VW have the same fixed point and total denominator exponent. By the exact-domain theorem they have the same nonempty positive cylinder. On any integer there, deterministic episode execution yields both concatenations. They have the same number of episodes, hence the strings WV and VW are equal. The commuting-words argument gives powers of a common primitive string: cancel the shorter prefix from the longer and induct on total length. Because both original words begin and end at r, the primitive string also returns to r. In particular, a first-return word has no internal visit to r and is primitive. Distinct first-return words cannot be compressed by identifying fixed points.

For a primitive P of charge D0 and fixed point p/u, define

    budget(m) = floor((v2(u m-p)-1)/D0).

At the fixed point the budget is infinite. Otherwise the exact-domain theorem and valuation transport prove that P^k is legal exactly when k<=budget. Thus budget is sufficient for the protected repetition language and minimal: two unequal budgets are distinguished by P^(smaller budget+1).

It is insufficient for arbitrary continuation. For P=[(2,1,2)], F=(9m+1)/8 and fixed point -1. Cofactors 15 and 31 both have budget one. Their original integers 59 and 123 become 67 and 139 after P. The next episodes reach 19 and 157: one descends below its original integer, the other does not. This is a concrete missing-continuation witness. Our macro retains the exact numeric exit.

## Unbounded recharge: a rejected global countdown

Let W=[(2,1,2)] and V=[(2,1,1),(1,1,2)]. Then

    F_W(m)=(9m+1)/8, F_V(m)=(27m+7)/32, J_W,V=-12.

For k>=2 and L>=3k+3 choose a positive odd z satisfying

    2^(L+5) z = 12 (mod 3^(2k+3)),
    mid=(2^(L+5)z-39)/27,
    m0=8^k(mid+1)/9^k-1, out=2^L z-1.

Such z exists by invertibility of 2 modulo the odd modulus, with oddness obtained by adding the modulus. The divisibility makes m0 integral. Moreover v2(mid+1)=2, so v2(m0+1)=3k+2, while v2(out+1)=L. Direct substitution proves W^k V maps m0 to out. The exact-domain theorem certifies execution. W grows, and the V prefixes are (9mid+1)/4 and (27mid+7)/32 in cofactor coordinates; their corresponding integer values are at least the original 4m0-1. This follows from mid+1=(9/8)^k(m0+1), k>=2, and 27*9^k>32*8^k. Odd shortcut stretches increase and even stretches have their minimum at the endpoint. Thus there is no intermediate descent in this block.

For k=2 the full map is (2187m+907)/2048>m. A small certified member has m0=169727, original n=678907, L=10, z=177, and exits at n=724987 after 11 shortcut steps. This integer nevertheless first descends at step 24 to 580646. This is not a divergent trajectory.

For k=8,L=27, m0=38112629721399295 becomes 82509295886794751; the defect valuation grows from 26 to 27 and its odd part from 567922439 to 614742159. Ordinary cofactor, countdown valuation, and odd defect part can all grow across an actual finite block. This excludes naive monotonic ranks in these coordinates. It does not exclude all possible ranks, nor establish an infinite sequence of resets. The parametric family is not claimed to occur after pullback stabilization; the separate census verifies many actual resets there.

## A safe executable capability

The exact power is

    F^k(m) = [p*2^(Dk) + A^k*(u*m-p)]/[u*2^(Dk)].

Return iterates are monotone: differences preserve their sign under the positive affine slope. Every shortcut prefix is also affine in m with positive slope. Therefore the minimum across all prefixes of all legal repetitions is obtained by evaluating all prefixes at the first repetition input if the return grows, or the last repetition input if it shrinks. The final endpoint is included. This proves an exact variable-repeat jump that preserves both exit and block minimum, permitting descent certification even when a macro's endpoint has risen again.

The implementation freezes first-return operators learned from B12, serializes and restores the bank, and selects a rule only from its exact current cylinder. First-return cylinders at the same r are disjoint by deterministic execution. All legal repetitions are compiled at once. If no operator applies, a raw episode is explicitly counted as fallback. Every macro is independently replayed with scalar T steps to check its endpoint and minimum. No wall-clock speedup is claimed.

## Frozen transfer and controls

Novel source means an integer absent from **every shortcut state** on the training paths, not merely absent from training roots. A same-training baseline compiles minimal first-descent cylinders from those exact paths. It is tested directly on each future source. No future operator is acquired.

| Protocol | Frozen operators | Future K | Evaluated roots | Novel sources closed entirely by frozen composition | Novel direct-baseline closures |
|---|---:|---:|---:|---:|---:|
| All 144 B12 roots | 134 | 16 | 1,363 | 2 | 0 |
| All 144 B12 roots | 134 | 20 | 15,870 | 7 | 0 |
| All 144 B12 roots | 134 | 24 | 172,868 | 48 | 0 |
| 100 B12 roots; 44 lineages held out | 102 | 16 | 434 | 1 | 0 |
| Same lineage holdout | 102 | 20 | 5,086 | 0 | 0 |
| Same lineage holdout | 102 | 24 | 55,734 | 9 | 0 |

The lineage split holds out B12 roots divisible by three and evaluates only future roots whose low 12-bit ancestor is held out. It is exploratory, devised after earlier corpus inspection, not a preregistered independent study. Every novel no-fallback success uses multiple macros. The full B24 run still uses 1,022,739 fallback episodes; the holdout uses 345,423. Closing the entire finite corpus with fallback is not frozen global closure. Macro compilation also performs arithmetic, cylinder selection, and verification replay. The baseline comparison isolates direct-cylinder lookup versus the new composed mechanism; it is not a comparison against every possible composed baseline.

The return census finds 1,108,356 B24 return occurrences, 102,015 distinct first-return words and exactly as many fixed-point classes. Equality of the latter counts is theorem-forced, not an empirical compression discovery. There are 203,267 cross-pattern valuation increases, including 154,042 after the checked pullback-stability threshold. Same-fixed-point countdowns remain valid; they do not transport across arbitrary changes of pattern.

## Verification and remaining obligation

Five unit tests and a separate verifier cover 7,380 bounded return words, 22,140 canonical/translated exact replays, 22,136 macro endpoint/minimum comparisons, and 2,048 budget controls. There are 81 duplicate fixed-point groups and zero primitive-rigidity violations. Deletion controls fail when removing the extra domain bit, charge D, injection J, or fixed-point exception. Sixty-one reset certificates include L=1024. An independent reviewer checked the mathematical argument and replayed 22,136 independent macro cases (translations 0, 1, 101; the verifier uses 0, 1, 10^20), including primitive normalization.

The CI workflow rebuilds all boundary exports and repeats tests, census, full frozen transfer, and lineage holdout from a clean checkout. Results are machine-readable alongside this report. This checkpoint has a nontrivial transferable operator and exact conditional domain theorems. What remains is an exhaustive finite recursive interface or a global well-founded argument covering arbitrary pattern switches, recharge, fixed points, and unresolved fallback. Neither authorized completion condition has been reached. No PR or main merge is part of this checkpoint.
