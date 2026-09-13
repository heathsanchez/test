# Hex V12 Repair-Schema Generality Selection — Sealed Result

## Verdict

**VERIFIED_REPAIR_SCHEMA_GENERALITY_SELECTION_AND_TRANSFER**

Workflow run: 34734314335  
Workflow job: 103662833064  
Head: `fe7b7c80cee0950f7c5160763980ad68d6e7233d`  
Evidence artifact: 10310427933  
Artifact ZIP SHA-256: `93f3446d125129f06f5326c74a1ad06e7a3addb2b5afef1ee1d0e079fa9a4f6a`

V12 removed V11's supplied anti-unification choice. Instead it generated four repair schemas from a two-axis description grammar:

- integer keys vs arbitrary keys;
- V10-observed batch sizes {1,2} vs arbitrary nonempty batches.

All four fit the exact V10 trajectory.

The exact sealed V11 transfer then eliminated precisely the two integer-key schemas because V11 used categorical string keys. Both arbitrary-key schemas remained.

A new tuple-like POSITION|TAG representation then exposed a first residual batch of size 3. That eliminated the V10-observed-batch schema. Exactly one schema survived:

`ANY_KEY + ANY_NONEMPTY_BATCH`

This is exactly the generality independently inferred by V11.

Using the selected schema, the new m=3,4,5 transfer worlds constructed a verifier-clean all-one policy with zero replay disagreements, all value-flip controls failed as required, and overwrite remained forbidden. Candidate-level semantic comparison cost was 5,632.

Held-out eight-relation data passed pinned HexGraphIso:
- positive: `route=witness n=34 nodes=2`
- negative: `route=certs n=34 records=2 recordsG=1 recordsH=1 autom=0`

Claim boundary: the two-axis schema-description grammar was still supplied.
