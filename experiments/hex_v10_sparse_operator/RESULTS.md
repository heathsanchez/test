# Hex V10 Sparse Meta-Operator Genesis — Sealed Result

## Verdict

**VERIFIED_SPARSE_META_OPERATOR_GENESIS_AND_TRANSFER**

Workflow run: 34733374359  
Workflow job: 103660225724  
Head: `6f66af5dadd1e99f6c0afa91c5277c38797c64f5`  
Evidence artifact: 10310401999  
Artifact ZIP SHA-256: `96059633cf1a53b94e5d631d1a4822413e2cab7b361cef50e8d3a05ed98c8f87`

V10 removed V8's supplied library of 16 complete Boolean selector operators.

The selector began as a fully undefined four-cell partial table. Development occurred only when a previously unseen observation pattern appeared:

- one relation exposed 11 and uniquely retained 11 -> 1;
- two relations exposed 10 and 01 and uniquely retained both -> 1;
- three relations exposed 00 and uniquely retained 00 -> 1.

The final table was [1,1,1,1], exactly matching V8. Every retained cell failed its earning-stage semantic test when flipped.

Candidate-level semantic comparison cost fell from V8's frozen 86,400 comparisons to V10's 13,504 comparisons, a 6.3981042654x reduction.

The completed sparse operator was then instantiated on held-out six-relation data and kernel-checked through pinned HexGraphIso:
- positive: `route=witness n=26 nodes=2`
- negative: `route=certs n=26 records=2 recordsG=1 recordsH=1 autom=0`

Claim boundary: the generic ability to add a value for a previously undefined observation pattern was still supplied.
