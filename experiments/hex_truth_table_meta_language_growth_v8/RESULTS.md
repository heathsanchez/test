# Hex Truth-Table Meta-Language Growth V8 — Sealed Result

## Verdict

**VERIFIED_META_LANGUAGE_PRIMITIVE_CONSTRUCTION_AND_TRANSFER**

Workflow run: 34732486735  
Workflow job: 103657718270  
Head: `b1f5a86afa41a0f3776ab79fb6de5e47c0914940`  
Evidence artifact: 10309732898  
Artifact ZIP SHA-256: `ee5512a9fa5cc70cbf967112944327adbfe30b310208da75d5aa580523eeaf3c`

The initial selector language contained only FIRST and LAST. Both had zero disagreement on the complete one-relation prior world, but each had 1,080 disagreements on the independently frozen two-relation consequence, certifying the old selector language inadequate.

All 16 anonymous binary Boolean truth tables over FIRST/LAST were then exhausted. Exactly two survived prior plus two-relation consequence:

- operator 14: [0,1,1,1]
- operator 15: [1,1,1,1]

The three-relation continuation exposed the previously unseen input pattern (0,0). Operator 14 then produced 16 semantic disagreements; operator 15 produced zero and was uniquely retained.

Every one-bit mutation of the retained table failed at the stage that witnesses that bit:
- flip bit 00: 16 disagreements at three relations;
- flip bit 01: 1,080 disagreements at two relations;
- flip bit 10: 1,080 disagreements at two relations;
- flip bit 11: failure on the one-relation prior.

The retained anonymous operator reproduces the behavior V7 named TRUE, but TRUE was not supplied in V8's initial language.

Held-out four-relation data was then compiled to HexGraphIso:
- positive: `route=witness n=18 nodes=2`
- negative: `route=certs n=18 records=2 recordsG=1 recordsH=1 autom=0`

Claim boundary: the complete 16-operator Boolean substrate remained supplied.
