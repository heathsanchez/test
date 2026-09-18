# Collatz post-DAG termination audit — 18 September 2026

**Collatz remains unproved.** This checkpoint records the exact reductions that
survived and the local ranking hypotheses that failed under RIGID filtering.

## Proven / exact reductions retained

1. Fixed-source refinement parameter:
   for (n=2^k q+b), one source-bit refinement sends
   [
   q'=lfloor q/2floor.
   ]
   Hence every fixed positive integer reaches the (q=0) boundary after
   finitely many refinements.

2. On the (q=0) boundary the fixed source is (b=n), and the concrete
   endpoint is (T^k(n)).

3. Universal lower merge remains sufficient:
   [
   orall n>1;exists x<n, exists a,b, T^a(n)=T^b(x)
   ]
   implies Collatz by ordinary strong induction.

4. Exact return-switch transport survives. For distinct same-anchor return
   words (W,V), if the new cylinder has excess (e) over its mandatory
   domain depth and the old/new separation is (h), then at the next
   distinct switch
   [
   h_{m next}=e+1.
   ]
   Thus drop lowers (h), recharge preserves (h), and flat raises (h).

5. A recharge target cannot immediately repeat. At recharge,
   (e=h-1), so after executing the target its own defect valuation is only
   (h<D_V+1), below its exact-domain requirement.

6. Any fixed non-fixed-point return word has a finite exact repetition budget
   from the 2-adic defect valuation. Periodic repetition alone therefore does
   not create an infinite ordinary trajectory unless the exact rational fixed
   point itself is realized.

## Refuted local finish hypotheses

### Raw finite DAG

The exact family
[
S_k=(k,2^k-1,k,3^k-1)
]
is RIGID for every (k), with (S_k	o S_{k+1}). Arbitrarily long segments
are realized by positive integers. A finite sound acyclic abstraction of the
unchanged raw RIGID transition relation is impossible.

### Minus-one classification

The exact edge
[
(2,3,2,8)	o(3,3,2,4)
]
is RIGID-to-RIGID and is not minus-one at the child.

### Scalar and one-episode ranks

On the fixed (q=0) boundary, endpoint size, endpoint excess, (k-c),
(v_2(d+1)), and odd count all fail to decrease on every RIGID edge.
Source (27) supplies a fully RIGID episode (71	o121) with multiplier
(27/16>1).

### Frozen per-anchor D/P trajectory bank

Training all component anchors through 65535 and freezing their exact
direct-descent / immediate-predecessor cylinders closes only 267 of 1905 new
anchors through 262143. First miss: 65583.

### Source-only universal grammar

Cross-valuation coalescence plus the q7 reverse-predecessor bank closes only
41 of 2722 component anchors through 262143 when applied at the source.
The useful lower merge is usually generated later along the orbit.

### Recharge graph acyclicity

At source range 16387..20481 a global recharge-pattern SCC appears:
[
(2,-1)leftrightarrow(2,7/23).
]
The opposite directions are witnessed by different sources, so this SCC is
not itself a concrete recurrent trajectory.

### Recharge-discharge contraction

This candidate is false even inside the exact RIGID boundary language.
Source 26863 has a RIGID recharge->drop block at anchor (r=1):
[
m:38773	o73609	o55207,
]
with composite map
[
mmapstorac{729m+467}{512}.
]
Its slope is (729/512>1), and (55207>38773). The source later directly
descends at shortcut step 42 to 15527; it is not a Collatz counterexample.

### Concrete pattern-cycle contraction

Also false. Source 16937 contains a concrete RIGID return-pattern cycle
(flat -> drop -> drop) returning to the same pattern node while
[
m:20629	o79399.
]
The exact composite is
[
mmapsto
rac{129140163,m+155923841}{2^{25}},
]
whose slope is (3^{17}/2^{25}>1).

Its exact fixed point is
[
-rac{155923841}{95585731}.
]
At entry (m=20629), the fixed-point defect has 2-adic valuation 26, while
the cycle charge is 25, so its exact repetition budget is one. The expanding
cycle is therefore a real separator to Archimedean cycle contraction, but it
cannot simply repeat forever from this entry.

## What the data now says

The successful bounded component-anchor census remains strong evidence:
through (2^{20}-1), 30,801 hereditary (q=0) RIGID sources collapse into
9,568 pre-descent coalescence components, and every component anchor has an
explicit lower certificate (6,417 direct descents, 3,151 immediate lower
predecessors, zero uncertified anchors).

This is not a theorem because the witness mechanism has not been made
universal.

The exact orbit-coupled q7 reverse-cone audit also closes every one of 2,722
component anchors through 262143:
1,701 by direct descent and 1,021 by a reverse-cone lower merge. This too is
bounded evidence only.

## Authoritative remaining theorem

After all local separators, the residual is no longer a finite-DAG problem or
a one-coordinate ranking problem.

A hypothetical minimal counterexample would have to realize an infinite
fixed-source (q=0) trajectory that

* never directly descends below its source;
* never meets any certified lower predecessor / lower-merge cone;
* survives Complete-O as an unresolved concrete exception;
* can switch return patterns indefinitely;
* may contain recharge, flat, and drop switches;
* may contain expanding recharge-discharge macros;
* may contain expanding concrete pattern cycles, though any fixed return word
  has only a finite repetition budget unless it is at an exact fixed point.

So the remaining statement is

[
oxed{
	ext{No positive ordinary integer realizes an infinite lower-merge-free,
RIGID, aperiodically switching return trajectory.}
}
]

Equivalently, one must supply either:

1. a genuinely global well-founded invariant that survives arbitrary pattern
   switches and exact recharge;
2. a universal recursive lower-merge constructor along the orbit;
3. or a proof that every infinite RIGID return language becomes periodic, in
   which case the exact repetition/fixed-point analysis can finish it.

None of those three statements has been proved here.

The current machinery has therefore finished **eliminating the false local
bridges**. Any next claim of global closure must address the aperiodic
fixed-source return language above directly.
