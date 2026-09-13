# V25 Verified Relational Isomorphism Decision via Hex

Verdict: **VERIFIED_RELATIONAL_ISOMORPHISM_DECISION_VIA_HEX**

Run: 34739514870  
Job: 103676706543  
Artifact: 10312372402  
Artifact SHA-256: `0d0525505ca51dd78e16d39a64404697cf7623c3688854b4409824fd9230da05`  
Main.lean SHA-256: `37b0cab3ad2f834d44c8046101fa5be98f8d11755732636965fd70010e57abb1`

Lean kernel checked four API theorems:
- `IncidenceNumberingPair.findSourceIso_isSome_iff`
- `IncidenceNumberingPair.sourceIsIso_eq_true_iff`
- `IncidenceNumberingPair.sourceIsIso_eq_false_iff`
- `IncidenceNumberingPair.sourceIso_of_findSourceIso`

So Hex's actual verified canonical/isomorphism search is now exposed as a sound-and-complete decision procedure for the relational structures represented by the V21/V24 incidence transport. A false Boolean result is proved to be a genuine source-level non-isomorphism, not search failure.
