# Forward witness audit — 16 September 2026

## Verdict and scope

The B24 representative census reproduces, but the tested forward-witness
representation does not approach a stable finite grammar. Almost all apparent
frozen transfer is recurrence of previously visited integers. Minimalizing the
witness horizon gives one genuinely novel source-integer transfer. Neither a
global Collatz proof nor completion condition B of the research brief is met:
the global programme has not been exhausted or reduced to a new proved
sufficient finite closure condition.

Base: `heathsanchez/test` commit `cc5d71145235ea7ca061bc472061df36569639df`.
Normalization reference: `dde95463d20f433b28898c129b18729926f152b8`.
RealityGraph reference: `e243c92b6221cd1cff115aa81012ad24b8ff794f`,
`prospective_capability_compounding.py`. Transferred practices: freeze before
future evaluation, source-only applicability, exact serialization restart,
and distinguish recurrence from novel-source generalization. No predictive
accuracy claim or learned statistical model is imported into the mathematics.

## Exact definitions

T(n)=n/2 for even n, and T(n)=(3n+1)/2 for odd n.
Exporter rows `(K,b,d,c,L)` retain the existing residual builder; Python checks
`T^K(b)=d`, the odd-step count c, and L=0 independently for every exported row.
This checks row semantics, not completeness of the existing reverse sieve.
All new arithmetic is arbitrary-precision Python integer arithmetic.

## Witness census

| K | Representatives | Raw tail edges | Unique integer edges | Max extra steps |
|---|---:|---:|---:|---:|
| 12 | 144 | 2,003 | 834 | 69 |
| 16 | 1,363 | 21,850 | 9,789 | 119 |
| 20 | 15,870 | 250,225 | 116,141 | 163 |
| 24 | 172,868 | 3,073,305 | 1,435,287 | 263 |

All representatives close. B24 endpoint-sensitive suffix interning still needs
2,404,648 nodes. Integer-edge sharing is about 2.14x, not convergence to a tiny
consequence grammar. The compiler stores caller-specific endpoints separately
from shared integer edges. The edge union is acyclic: a cycle with minimum m
would trap any first-descent witness providing its outgoing edge, although that
witness must end below its root b<=m. This is impossible by determinism.

## Finite forward cylinder lemma (mathematical proof, not Lean-checked)

A length-t parity word has a unique residue r modulo M=2^t. On that cylinder,
T^t(n)=(A n+B)/M, A=3^a and B>=0. Induction proves this: at step j an even
step preserves A,B and an odd step sends `(A,B)` to `(3A,3B+2^j)`.
Inputs agreeing modulo 2^t have the same t parities, by induction on the
divisibility of their successive differences.

For A<M, strict descent is precisely n>B/(M-A), equivalently
n>=floor(B/(M-A))+1. Every positive actual descent forces A<M because
A n+B<M n and B>=0. Thus the old direct-witness slope check is redundant once
actual descent has been established. This is not a claim that slope alone
always implies descent.

`validate_rule` independently reconstructs A from the odd count and B from
scalar replay at residue r. It rejects forged coefficients and thresholds.
`applies` assumes already validated/generated tuples; it is not itself a
certificate checker. No external rule files are consumed by this experiment.

## Frozen transfer and leakage control

The endpoint-suffix library learned from B12/B16/B20 has 250,743 distinct rules.
It covers 16,602 B24 representatives, all of which had appeared as source
integers within earlier training trajectories. Excluding only earlier roots
would misleadingly label 5,846 of those as new. This is recurrence, not novel
source transfer. The stronger source exclusion includes every trained internal
trajectory state. It still does not establish disjoint hereditary lineages.

Replace each long suffix by the source's first strict descent (using an exact
next-smaller-element stack). The library shrinks to 35,383 rules. Serialization
and restart preserve it exactly. It covers 16,603 B24 representatives, including
one of 156,266 novel source integers. B16 and B20 novel-source coverage is zero.
Deleting all rules trivially returns zero coverage; no strong causal claim is
made from that baseline alone.

The novel source is 13,822,111. Its rule was learned from source 282,257,567 at
offset 36 of the trajectory of B20 root 847,871. Both share residue 13,822,111
modulo 2^27. The exact reusable theorem is

    n = 13,822,111 + 134,217,728 q, q >= 0
    => T^27(n) = (129,140,163 n + 217,068,515) / 134,217,728 < n.

The descent threshold is n>=43. At q=0 the endpoint is 13,299,211.
This theorem covers an infinite cylinder, but not all residual constructors.

## Fixed-word obstruction (mathematical proof, not Lean-checked)

For n_m=2^m-1 and 1<=j<=m,

    T^j(n_m)=3^j 2^(m-j)-1 > 2^m-1.

Before each step the value is odd; the identity follows by induction, and the
inequality follows from 3^j>2^j. Therefore any finite library of fixed-length
forward descent certificates with maximum length H misses every n_m with
m>H. No amount of exact sharing or lookup minimization removes this limit.

This does NOT exclude finite parameterized theorems, recursively composed
grammars, unbounded return times, or capabilities that permit intermediate
growth. A complete system must supply one of those mechanisms and prove its
well-founded progress, rather than merely enlarging this fixed-word library.

## Normalized reverse language audit

For n(t)=2^K 3^r t+b with known image 3^(c+r)t+d, a reverse state is
y(t)=2^u 3^v t+D. With w=v-r the slope condition is exactly
2^u 3^w<=2^K. E sends (u,w,D) to (u+1,w,2D). O sends it to
(u+1,w-1,(2D-1)/3), requiring w+r>=1 and D=2 mod 3. An O-run of length m
requires m<=w+r and 3^m dividing D+1; its intercept is
2^m(D+1)/3^m-1. These conditions establish integral, odd, positive predecessors.

w never increases, so endpoint rho=max(0,-w) is exactly the minimum refinement
resource for the whole path. Pareto dominance in (rho,D) preserves queries
rho<=r and D<b, for endpoints already meeting the slope test. The resulting
certificate proves a smaller positive coalescing predecessor, usable by strong
induction; it is not a direct forward-descent path from n.

Crucial scope: refinement r covers original parameters q=3^r t. It does not
cover arbitrary q. A certificate for q=0 at some refinement does not cover
all children, especially q coprime to 3. Executable bounds K<=24,R<=80 and
intercept-overflow exits are not universal mathematics.

## Remaining proof obligation

The missing bridge is a proved constructor-closed system covering every
parameter of every retained residual family, with each certificate providing
either strict descent or a smaller positive coalescing predecessor under a
well-founded induction. No such system has been synthesized here. Simply
quantifying the observed q=0 behavior over every depth restates an unproved
global claim; it does not establish a reduced final lemma.

The fixed-word route is decisively limited. One justified continuation is to
parameterize the long odd-run constructor (already known algebraically as
2^r m-1 -> 3^r m-1) and prove progress after a variable return, while retaining
cofactor/refinement coverage. Naive lexicographic episode ranks fail:
(r,m) increases from n=9: (1,5)->(3,1), and (m,r) increases from n=7:
(1,3)->(7,1), after the odd block and all immediately following even steps.
These are rank counterexamples, not Collatz counterexamples.

## Reproduction

    g++ -O2 -std=c++20 -Wall -Wextra -Werror experiments/collatz_export_boundaries.cpp -o /tmp/export-boundaries
    mkdir -p /tmp/collatz-witness-audit
    for k in 12 16 20 24; do /tmp/export-boundaries "$k" > "/tmp/collatz-witness-audit/b${k}.csv"; done
    python experiments/test_collatz_witness_compiler.py
    python experiments/collatz_witness_compiler.py /tmp/collatz-witness-audit/b12.csv /tmp/collatz-witness-audit/b16.csv /tmp/collatz-witness-audit/b20.csv /tmp/collatz-witness-audit/b24.csv --out /tmp/collatz-witness-audit/witness.json
    python experiments/collatz_minimal_witness_transfer.py /tmp/collatz-witness-audit/b12.csv /tmp/collatz-witness-audit/b16.csv /tmp/collatz-witness-audit/b20.csv /tmp/collatz-witness-audit/b24.csv --out /tmp/collatz-witness-audit/minimal.json
    python experiments/collatz_structural_audit.py

The full compiler uses substantial memory for millions of exact rules. Large
rule export is optional. The compact checked-in results contain input and edge
hashes. This is a research checkpoint, not a global proof manuscript.
