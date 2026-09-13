# V23 Composed Relational Transport to Hex

Verdict: **VERIFIED_RELATIONAL_ISOMORPHISM_TO_HEX_COMPOSITION**

Run: 34739086129  
Job: 103675577303  
Artifact: 10312157009  
Artifact SHA-256: `e653cffab8548e9d061def7c4d95c078cb523999b37e4a70f4a97d2ac2f762ba`  
Main.lean SHA-256: `7d170aeafeb4c034ef7b6a9201dc28f267e51b56c91a6fa9736daf5a96516160`

Lean kernel checked:

`IncidencePairPresentation.sourceIso_iff_hexIsomorphic`

This composes the V21 general incidence theorem with the V22 concrete Hex compiler. For arbitrary relational signatures with finite arity, any exact finite presentation of the identity-anchor + occurrence incidence structure is isomorphic at source level iff its compiled Hex `Colored` graphs are isomorphic.

Remaining boundary: automatically construct the exact finite incidence presentation from only finite numberings/color coding rather than supplying its color/adjacency correctness fields.
