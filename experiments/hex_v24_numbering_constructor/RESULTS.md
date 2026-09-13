# V24 Incidence Numbering Constructor to Hex

Verdict: **VERIFIED_INCIDENCE_NUMBERING_CONSTRUCTOR_TO_HEX**

Run: 34739257736  
Job: 103676029059  
Artifact: 10311753570  
Artifact SHA-256: `e31cf7b5fe5e52002fc6131331fce93544bcbdae78690d7f51030e50a781ae69`  
Main.lean SHA-256: `c6cddb808379b3b13db8f953ed847660a64c7c1ae814879f5525859a033f128b`

Lean kernel checked:

`IncidenceNumberingPair.sourceIso_iff_hexIsomorphic`

The exact finite incidence presentation is now constructed rather than supplied. The remaining inputs are only:
- bijective numberings of the two finite incidence-node sets by the same `Fin n`;
- one common injective ordered color code into `Fin k`;
- onto witnesses that the used semantic colors cover that code.

Adjacency, looplessness, symmetry, semantic color correctness, the V21 incidence theorem, and the V22 Hex compiler are all proved inside the chain.
