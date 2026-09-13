# V22 Verified Finite Compiler to Hex

Verdict: **VERIFIED_FINITE_COLORED_COMPILER_TO_HEX**

Run: 34738896421  
Job: 103675093770  
Artifact: 10312111874  
Artifact SHA-256: `8fb25a44cf6c2d0feef17007033a8b8274694634000af19eade1045916017595`  
Main.lean SHA-256: `a1add522f8a2bd291c6c9067cd4d714ac92c12c702a7ea4bb2fbbd69aefa6ad8`

Lean kernel checked:

`finiteColoredIso_iff_hexIsomorphic`

For arbitrary finite-colored graph presentations on arbitrary vertex types, once explicit bijective numberings by `Fin n` are supplied, abstract color/adjacency-preserving isomorphism is equivalent to Hex's concrete `Colored n k` isomorphism.

This closes the generic numbering/compiler boundary to Hex. The remaining composition step is to instantiate this compiler with the V21 incidence representation.
