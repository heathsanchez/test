# Collatz RIGID transition audit — 18 September 2026

**Collatz remains unproved. This audit closes two proposed shortcuts by
counterexample and proves a universal obstruction to a finite acyclic
abstraction of the current Complete-O plus direct-descent failure machine.**

It also supplies the correct fixed-integer countdown for the all-odd
source-refinement family. Leaving this family need not produce a lower merge.
The algebraic proofs below are human-readable proofs, not Lean certificates.

## Source and execution

Audited source: `a902da9241d899bbb9d96b927459e6d0cf421f4b`, branch
`collatz-rigid-lift-v1`, in `heathsanchez/test`.

The requested separator run
[35290366984](https://github.com/heathsanchez/test/actions/runs/35290366984)
was cancelled after its five-minute job limit. It did not establish the
minus-one transition claim.

The original `phi` represented an infeasible reverse state with a score
whose step count was one billion. Its caller then evaluated `1 << tail.S`.
A regression test reproduces the resulting `MemoryError` under a 64 MiB
address-space limit at `phi(2,1)`, whose true optimum is only `(4,7)`.

The fix represents infeasibility by `None`, skips infeasible tails, and
rejects a classifier result worse than its source baseline instead of
silently labelling it RIGID. It changes no feasible Bellman objective.

After this fix the original depth-9, precision-4 probe reports:

| Quantity | Result |
|---|---:|
| RIGID-to-RIGID transitions | 119 |
| Both endpoints minus one at the tested precision | 15 |
| Other RIGID-to-RIGID transitions | 104 |
| Transition signatures | 47 |

These are bounded discovery results. In particular, the 104 transitions
refute an unrestricted local claim; they do not by themselves refute a
separately defined persistent-recurrence claim.

## 1. A small exact separator: the source 3

Use the shortcut map `T(n)=n/2` for even `n` and `(3n+1)/2` for odd `n`.

The source-refinement edge with bit zero is

\[
(k,b,c,d)=(2,3,2,8)\longrightarrow(3,3,2,4).
\]

Indeed, `3 -> 5 -> 8 -> 4`, and the cylinder identities are

\[
T^2(4q+3)=9q+8,\qquad T^3(8q+3)=9q+4.
\]

For the parent, the only word with two positive exponents and total cost
at most two is `(1,1)`. It has score `(2,5)` and reconstructs 3 from 8.

For the child, `(1,1)` is illegal: `(4*4-5)/9=11/9`. At total cost three,
`(2,1)` has cocycle 5 and reconstructs `(8*4-5)/9=3`, whereas `(1,2)` has
cocycle 7 and is illegal. Thus the optimum is `(3,5)`.

Neither endpoint is below 3. Both states are exactly RIGID. But the
endpoint residues change from `8 mod 9` to `4 mod 9`; even modulo 3 the
child is 1, not minus one.

Therefore:

\[
\mathrm{RIGID}(S)\land\mathrm{RIGID}(S')
\not\Rightarrow \text{both endpoints are minus one}.
\]

The source 3 later descends. This witness concerns the local implication,
not infinite persistence.

## 2. Universal all-odd RIGID family

For every integer `k >= 1`, set

\[
S_k=(k,2^k-1,k,3^k-1).
\]

For `0 <= t <= k`, exact iteration gives

\[
T^t\bigl(2^k(q+1)-1\bigr)
=3^t2^{k-t}(q+1)-1.
\]

The first `k` source steps are all odd, so this is a valid cylinder.
Its boundary endpoint `3^k-1` exceeds `2^k-1`, so direct descent does
not close it.

A complete reverse word contains exactly `k` actions with positive
exponents. Consequently its total cost is at least `k`. The only word
attaining `k` is `(1,...,1)`. Its cocycle satisfies

\[
C_0=0,\quad C_{j+1}=2C_j+3^j,
\quad C_k=3^k-2^k.
\]

Its reconstruction of the boundary is

\[
\frac{2^k(3^k-1)-(3^k-2^k)}{3^k}=2^k-1.
\]

Thus it is feasible, uniquely minimizes the total cost, and matches the
source score exactly. **Every `S_k` is RIGID.**

The exact bit-one source refinement maps `S_k` to `S_(k+1)`: its raw
endpoint is `2*3^k-1`, and the odd child endpoint is `3^(k+1)-1`.

This proves an infinite symbolic RIGID chain. Each finite initial
segment is realized by an ordinary positive integer: choose
`n=2^M-1` with `M` larger than the final depth. Starting at depth two
ensures a boundary source greater than one.

## 3. No finite sound acyclic abstraction of these raw transitions

Suppose a finite graph with `N` vertices represents every RIGID edge of
the current machine, including the family above, via one consistent state
map `alpha`: every concrete edge `s -> s'` induces the graph edge
`alpha(s) -> alpha(s')`, including self-loops. A concrete path with
at least `N` edges maps to a graph walk visiting `N+1` vertices. Some
vertex repeats, producing a directed cycle.

Therefore no such finite graph can be acyclic. This remains true if
coverage is restricted to finite paths realized by ordinary positive
integers, since those paths have unbounded lengths.

The obstruction is stronger than a bounded SCC observation. It follows
from an explicit family and a pigeonhole argument. Restoring finitely
many distinctions cannot make the unchanged transition relation a DAG.

Possible changes to the proof architecture are:

1. retain unbounded integer data and prove well-foundedness;
2. replace finite runs by justified macro-transitions;
3. add a sound lower-merge constructor that closes this family.

This theorem applies to the current Complete-O/direct-descent classifier.
It does not rule out a different certificate language or a different
transition system.

## 4. The correct countdown belongs to a fixed integer

An obligation for one fixed source should retain its cylinder parameter:

\[
n=2^k(q+1)-1,\qquad T^k(n)=3^k(q+1)-1.
\]

To follow the bit-one edge while preserving this `n`, `q` must be odd,
and

\[
q'=(q-1)/2,\qquad
v_2(q'+1)=v_2(q+1)-1.
\]

The same quantity is the ordinary endpoint's odd-run budget, because
`3^k` is odd:

\[
v_2\bigl(T^k(n)+1\bigr)=v_2(q+1).
\]

Thus a fixed positive integer cannot follow the all-odd family
indefinitely. Its number of consecutive bit-one continuations is at
most the current `v_2(q+1)`.

This corrects the source-refinement/endpoint distinction. The boundary
endpoints `d_k=3^k-1` are all even; applying an odd-step countdown directly
to `d_k -> d_(k+1)` would be invalid. It is the actual endpoint
`3^k*q+d_k` that undergoes the ordinary odd step for a bit-one child.

Also, the compatible congruences `d_k = -1 mod 3^k` concern changing
integers. Their 3-adic limit is minus one, but no contradiction follows
from that alone. Fixed-source consistency is the essential extra fact.

## 5. Leaving the family does not finish the obligation

For every `k >= 1`, the bit-zero child is

\[
E_k=(k+1,2^k-1,k,(3^k-1)/2).
\]

It too is RIGID. Here is a direct proof.

The endpoint `(3^k-1)/2` is `1 mod 3`. Legality of the first reverse
action therefore requires an even exponent: `a_1 >= 2`. Every remaining
exponent is at least one, so total cost is at least `k+1`. Equality
forces the unique word `(2,1,...,1)`. Its cocycle is `3^k-2^k`, and it
reconstructs exactly `2^k-1`. Thus the unique optimum has score
`(k+1,3^k-2^k)`.

Finally `(3^k-1)/2 >= 2^k-1` for `k >= 1` (equality only at `k=1`),
so the child is not direct descent. It is RIGID, while its endpoint is
`1 mod 3`, not minus one. This gives an unbounded family of exact
non-minus-one RIGID transitions.

An odd-run countdown therefore proves departure from one family, not
termination of the whole failure machine. Once a zero source bit is fixed,
the exact all-odd source family cannot be re-entered. Further odd runs and
transitions through other unresolved residual regions still require proof.

## 6. The remaining proof obligation

The lower-merge induction and the exact cylinder/child algebra remain
useful. What this audit does not supply is a universal proof that a fixed
positive integer cannot continue through other unresolved RIGID states
after leaving the all-odd source family.

The revised target is a sound termination argument for obligations
retaining the fixed source (or its parameter). One valid route is a finite
sound graph that retains cycles, with a well-founded rank decreasing on
every concrete internal edge of each reachable SCC. The SCC condensation
is a finite DAG, so after leaving an SCC a path cannot return to it.
Proving finite residence in every SCC would therefore suffice.

The countdown in this audit covers only the all-odd source-family edges;
it has not been shown to cover every internal edge of a universally sound
SCC. Finite visits to an arbitrarily selected ranked region are weaker:
such regions, unlike actual SCCs, may be revisited indefinitely. Other
routes are a global well-founded measure or sound new lower-merge
certificates that remove the remaining obligations.

If this replaces the proposed finite DAG by a graph with unbounded
numeric ranks, a globally finite union of tail exceptions must be proved
separately; finite control alone is insufficient. One must establish a
finite cover or prove a uniform certificate theorem for the exception
obligations.

**No universal lower-merge theorem, no universal termination theorem,
and no Collatz theorem is claimed.**

## Reproduction

```sh
python -m unittest discover -s experiments -p test_collatz_bellman_audit.py -v
python -u experiments/collatz_bellman_rigid_transition_probe.py --depth 9 --j 4
```

The tests include independent rational replay of every complete reverse
word no longer than each odd source cylinder through depth eight (255
source cylinders), the infeasible-state allocation regression, the source
3 separator, fixed-source countdown witnesses through 40 all-odd steps,
and RIGID even-exit witnesses through depth eight. These tests support
the implementation; the universal family and graph obstruction rest on
the algebraic proofs above.
