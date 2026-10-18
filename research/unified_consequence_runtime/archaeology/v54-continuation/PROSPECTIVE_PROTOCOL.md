# Draft prospective frontier — NOT FROZEN, NOT RUN

Status: **DRAFT ONLY. Root V54 must first pass its required qualification.** This document does not select, freeze, execute or admit a candidate, and is not evidence of future blindness. Root must consider the additional ROS anchors before any choice.

## Source-derived question

Can a retained language admit, independently reverify, reload and use a previously absent arity-five Boolean schema using the existing DevelopmentalIR V6 generic APIs? This is a finite schema extension question. It does not claim natural-world source transfer or O1-dependent O2 discovery.

Exact source: Triskelion `644f83bb98f772f395b112ca4a6a5a81b3e98c6b`, `experiments/developmental_ir_v6_blind_grammar_expansion.py`, SHA256 in `TRISKELION_INDEX.json`. Existing operations: `expr_eval_abstract` 44, `expr_eval_actual` 53, `expr_cost` 60, `Op` 97, `make_node` 197, `recover` 239, `verify` 243, `Installed` 249, `language_hash` 257, `evaluate` 261. Existing serialization/reverification/reload pattern is 381–395.

## Unexecuted candidate nomination

An exact draft expression that needs no new semantic algorithm is:

`D(D(x0,x1),D(x2,D(x3,x4)))`

Its native representation is the existing nested `('D', left, right)` tuple form; native ground semantics remains `D(a,b)=not(a) and b`. No truth table, result, task outcome, or timing was computed here. Its (arity5, truth-table) key cannot be a historical V6 installed key because the committed language uses only arities2/3/4. Essential dependence on all five formal arguments must be checked after an actual prospective freeze, not assumed from syntactic variable occurrence.

This expression is now exposed in this conversation/document. It may serve as a nominated prospective test only after explicit protocol review; it cannot later be described as an unseen independent challenge. A truly unfamiliar challenge requires an independently selected expression/identity after the mechanism is frozen, with no output inspection or adaptive selection. Candidate generation must reuse existing D-expression composition/selection semantics; no new solver or domain-specific method is authorized by this draft.

## Deferred sequence if root chooses this scope

1. Require successful root V54 qualification and complete ROS anchor review. Freeze source hashes, exact target expression(s), producer-visible inputs, candidate budget, exclusions and output schema before any native evaluation.
2. Recover the historical portable V6 language from committed data, independently reverify through native `verify`, and record baseline language hash. Do not rerun `run_once` and relabel its historical 10,000 tasks prospective.
3. For each new arity5 schema, derive its key through native `expr_eval_abstract(e,5)` and reverify with native `verify(key,e)`. A deliberately mismatched table must be rejected using the existing verifier. This checks consistency within the same interpreter; it is not a new independent natural-domain oracle.
4. Use only the existing admission rule from `run_once:313–340`: encounter count>=3, utility=count*max(expanded_D_cost-1,0)>=6; at most24 installed keys; replace the least-utility installed key only when candidate utility is strictly higher; admit only with a successful native verification digest. The generic helper APIs support this, but the frozen entrypoint's 2/3/4 bookkeeping does not. Any adapter must be explicit and reviewed; do not silently modify the historical algorithm.
5. Compose heldout task trees through native `make_node` with nontrivial argument subtrees and repeated variables, keeping comparison inputs identical. Compare old frozen keys, admitted new keys, matched wrong/unused key, no-warrant and candidate-ablation arms through native `evaluate`. Native `direct==expanded` must hold for every task.
6. Serialize the installed language with original fields, clear runtime state, independently reverify each entry, reconstruct `Installed`, and require identical `language_hash`, outcomes and cost. Report VERIFY/PROMOTE/eviction overhead separately.
7. Report the result as finite schema admission/reuse only. Do not assert V54-style new-operator discovery: `recover` reads the supplied expanded expression, so an ancestor-dependent discovery gain is not measured. That stronger frontier remains UNKNOWN until an existing qualified mechanism and source-distinct prospective harness are located.

## Practical and authority boundaries

DIR V7 `0b0bc66f908469fdb5b13a9d6cfc4c4fcee20c3a` already records failed native binary-size/hybrid-runtime gates. Symbolic D-cost savings do not establish practical superiority. Any practical claim needs the existing V7 expanded/inline/outline/hybrid compiler comparison under matched workload and total cost, with old negative retained.

All proposed actions remain inside user-authorized local research effects. Scientific verification never expands user action authority. Global nonbypassability remains UNKNOWN as explained in `AUTHORITY_ASSESSMENT.md`.
