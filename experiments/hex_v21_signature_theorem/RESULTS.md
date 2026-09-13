# V21 Arbitrary Relational-Signature Incidence Theorem

Verdict: **VERIFIED_ARBITRARY_RELATIONAL_SIGNATURE_INCIDENCE_THEOREM**

Run: 34738402758  
Job: 103673798884  
Artifact: 10311727328  
Artifact SHA-256: `a9031932d6e7e1e4d815089251026de82d0c750c4656d7e200866544830c8dc9`  
Main.lean SHA-256: `5b6273fd4d49c1863cf9c25ed379cc4af878b1dfa6d930f288a2ea94ece54191`

Lean kernel checked `sourceIso_iff_incIso` for:
- arbitrary carrier types;
- arbitrary relation-symbol type;
- arbitrary finite arity for each relation symbol.

The theorem states that one carrier bijection preserves all source relations iff there is a color- and adjacency-preserving isomorphism of the identity-anchor + relation-occurrence incidence representation. The theorem is stronger than the finite-signature target: it does not require the relation-symbol type itself to be finite.

Remaining boundary: compiling a finite incidence structure into Hex's concrete `Colored n k` numbering without changing isomorphism.
