# Verified Retention-Policy Genesis V1 — Result

## Verdict

**NEGATIVE / PARTIAL.** The finite grammar constructed a legal, set-valued retention policy that beat every single-coordinate heuristic on twenty unseen streams. A certified regime-change residual also constructed a behaviorally distinct revision that improved twenty untouched post-change streams. The initial generated policy did **not** beat the frozen hand-written geometry policy: 104,887 versus 102,578 charged reconstruction cost.

## Evidence

- Grammar: 6,561 programs; 26,244 verifier calls for genesis and 26,244 for revision.
- Feasible dependency-closed retained subsets: 27 at capacity four.
- Generated policy: 104,887.
- Best scalar (`breadth`): 111,358.
- Frozen hand geometry: 102,578.
- Hindsight oracle: 100,000.
- Post-change old policy: 164,113.
- Post-change revised policy: 117,159; revision ablation penalty 46,954.

## Claim boundary

Verified bounded policy construction and proof-triggered revision, but **not** verified superiority to the supplied geometry policy. The result therefore does not establish autonomous retention-policy genesis as a replacement for the last hand-written judgment.
