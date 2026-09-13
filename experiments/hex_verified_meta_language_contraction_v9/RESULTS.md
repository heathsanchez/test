# Hex Verified Meta-Language Contraction V9 — Sealed Result

## Verdict

**VERIFIED_META_LANGUAGE_CONTRACTION_AND_TRANSFER**

Workflow run: 34732916564  
Workflow job: 103658940710  
Head: `ffa58bd5ffb64f24042f72ec7d774d9ab32b0f60`  
Evidence artifact: 10309587400  
Artifact ZIP SHA-256: `7237bd837d484d662c64846b5cea518ced93146cd098be8803188f3f5908103b`

V9 asked whether the FIRST/LAST scaffolding used to construct V8's selected truth table still had to persist.

The selected V8 table [1,1,1,1] factors through the empty input projection. The unique minimum dependency set therefore has cardinality 0, contracting the retained selector from two inputs to a zero-input constant output 1.

Exact semantic replay stayed at zero disagreement on the one-, two-, and three-relation qualification worlds.

The V8 runner-up [0,1,1,1] provides the sham control: it does not factor through zero inputs, FIRST alone, or LAST alone; it requires both inputs. Thus contraction is licensed by the selected operator's learned semantics, not by the test harness.

Replacing the contracted output 1 with 0 restored 36 disagreements on the one-relation world.

The contracted selector was then used without FIRST/LAST computation on held-out five-relation data and kernel-checked through HexGraphIso:
- positive: `route=witness n=22 nodes=2`
- negative: `route=certs n=22 records=2 recordsG=1 recordsH=1 autom=0`

This establishes bounded verified contraction: developmental scaffolding can be deleted after consequence proves the retained result no longer depends on it.
