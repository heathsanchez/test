# RIGID lift theorem audit

The local arithmetic lift is exact:

* among the three lifts of -1 mod 3^j, exactly one is -1 mod 3^(j+1);
* an odd shortcut step preserves -1 mod 3^j;
* an even shortcut step exits it;
* ordinary integers have only finitely many consecutive odd shortcut steps.

However, none of these facts implies that **Bellman RIGIDITY** selects the unique
minus-one lift.  That implication is the remaining mathematical theorem, not
an algebraic consequence of the residue lift itself.

## Do not conflate the two transition systems

There are two different transitions:

1. source-cylinder refinement: b mod 2^k -> b or b+2^k mod 2^(k+1);
2. shortcut evolution of an endpoint d -> T(d).

The identity d == -1 mod 3^j -> T(d) == -1 mod 3^j on an odd step concerns
(2).  The SCC probe is built from (1).  A proof must derive how the Bellman
score and endpoint residue transform under source refinement before using the
odd-run countdown to break a cycle.

This is the current smallest exact obstruction.

## Required next lemma

For a concrete RIGID source state S=(k,b,c,d), derive exact formulas for each
child S_0,S_1 under one source-bit refinement, including:

* c' and d';
* source score (k+1,Csrc');
* Bellman comparison at c';
* whether RIGID can persist.

Only after those formulas are proved may recurrent RIGID child selection be
identified with a 3-adic residue lift.

No global Collatz conclusion is authorized before this bridge is established.
