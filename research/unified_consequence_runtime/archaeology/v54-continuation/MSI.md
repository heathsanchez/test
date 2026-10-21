# MSI and consequence-selection source recovery

Read-only recovery on 2026-10-15. Exact local git blobs were read; no native scientific experiment, Lean recompilation, remote request, upstream write, or V54 source edit was performed. Source extracts and SHA256 values are in `MSI_INDEX.json`.

## Exact native MSI substrate

All MSI paths below are pinned to `5d448c0ecc82ff3945d009963064ebbb67d2f308` (local HEAD; 2026-09-01, consequential-core minimal-representation certification update).

| Native source | Exact API | Integration consequence |
|---|---|---|
| `consequential_core.py` | `PairResidual:86`, `ClosureResidual:106`, `AcquisitionResidual:126`, `DevelopmentState:154` | Keep pair separation, language non-realizability, and bounded acquisition failure separate. State is `(carrier,E,H,C,D)`; one kind of residual cannot stand in for another. |
| same | `RefineRepresentation:169`, `ReplaceVersionSpace:174`, `ExtendLanguage:179`, `UpdatePolicy:184`, `CoupledRepair:189` | Native operations already distinguish changes to representation, live hypotheses, executable language, and acquisition policy. |
| same | `residual_belongs_to_state:258`, `certify_repair:271`, `compile_repair:289`, `ablate:321` | Reject stale C/D evidence and nonconservative/unattached repair; compilation returns exact before/after provenance. Exact ablation only applies when current state equals token.after. |
| `consequential_version_space.py` | `coarsest_representation_repairs(state,residual,dynamics):41` | Complete finite partition enumeration, filters strict lawful residual-resolving refinements, returns all with maximum retained equivalence pairs. |
| same | `discriminating_pairs(repairs):70`, `update_version_space_from_pair_answer(repairs,pair,observed_same=...):91` | Smallest existing next-observation machinery: return only pairs on which remaining repairs disagree; filter by actual answer. Deterministic first returned pair requires no new learned router. |
| `consequential_certification.py` | `certify_representation_repair:40` | Requires coarsest-lawful membership and, if H supplied, unique survivor from the experiment answer. |
| same | `certify_finite_table_language_extension:96` | Binds delta to executable table and computes kernel and quotient lawfulness, stronger than trusting caller booleans. |
| same | `certify_kernel_policy_update:127`, `certify_policy_update:150` | First binds D to block-size fingerprint of supplied source kernel plus warm success; latter trusts external warm verification. Neither establishes unrestricted expressivity. |

The generic `certify_repair` accepts a callback and string verifier tag. It is an in-process certification interface, not an authenticity or security monitor. A repair object bearing the string `verified` does not by itself confer authority.

## Native developmental experiments: callable boundaries and limits

`tests/test_constructor_genesis.py` has directly callable `closure:14`, `generate_terms(max_depth=3):27`, `first_counterexample:65`, `learn_constructor(algebra,n,max_depth=3):77`, `identity_holds:106`, `assoc_holds:116`. Candidate language is `x | F(t) | G(t)`; all 15 depth-three syntax trees are generated. It learns operative composition on the reachable finite algebra; the hidden verifier explicitly evaluates true composition. Historical 729-world census in `CONSTRUCTOR_GENESIS.md` is already exposed and should not be billed as a fresh frontier.

`tests/test_endogenous_genesis.py` exposes `all_map_signatures(n):7`, `action_closure(generators,n):15`, but `synthesize_o1` and `discover_o2` are nested inside test method `test_residual_driven_o1_genesis_can_enable_autonomous_o2:55`, at lines 98 and 116. It searches all three-state maps for residual repair and maximum count of newly enabled capabilities. Turning those nested functions into a production API would be implementation work, not recovery. Historical 648 causal witnesses are a bounded finite census; do not repeat as a new discovery.

`tests/test_generated_constructor_genesis.py` exposes `behavioural_generate(max_depth):34`, `combine:70`, `repairs:74`, `synthesize(tasks,max_depth=8):86`; NOT/AND substrate generates at most 16 binary Boolean behaviours. Historical parity tasks and permuted presentation at lines 79/111 are already exposed. This is not native code constructor V103/V104 and cannot stand in for them.

`tests/test_recursive_developmental_compounding.py` exposes `residual:40`, `query_fingerprint:56`, `cold_episode:80`, `compile_policy:98`, `policy_episode:118`. It learns average residual separation by anonymous observation balance fingerprint. Source and target literal query IDs differ; every arm shares the same target C and one-query budget. Historical WARM t2 versus others t0 is policy-guided bounded acquisition, not a new language/expressivity result. Both tables are committed and already inspected.

`tests/test_blind_recursive_cross_grammar_genesis.py` exposes `synthesize_costs:53`, `synthesize_programs:97`, `frozen_task_split:146`, `discover_interface(grammar,training):158`, `learn_doubling_interface(block,block_width):252`. Existing training masks, 96 heldout masks, sealed adder family and width 2/4/8 promotions are historical, not newly blinded here. `lean/BlindRecursiveCrossGrammarGenesis.lean` certifies exact frozen Boolean programs and finite six-bit/cut-carry cases. Increasing width beyond those cases would require a new verifier qualification; do not inherit the finite Lean certificate by analogy.

`tests/test_final_boss_task_only_category_genesis.py` exposes `choose_query(candidates,queries,asked):152`: minimize largest yes/no branch, imbalance, sequence length, then query identity. `identify:167` applies it against a finite hypothesis universe. This is an existing balanced discriminating-query selector, but constructing a new task-specific world universe is not free discovery.

## JPL/native consequence selection

Exact `test@52eb1e7995bd877a2b698efe1883ae2b80a03737`, `research/mathgraph_minimal_quotient/h11_quotient.py`:

- `minimal_basis(vectors,labels):235` searches observation-coordinate subsets in increasing cardinality. It keeps the first subset whose projections preserve the number of distinct full vectors. This is an actual exact minimum finite observation-basis selector and can operate on existing method outcome vectors without changing the synthesis method.
- `quotient(results,mode):249` packages that basis for four transport schedules or six declared continuations. `build_cases:44`, `categorise_event:110`, `run_wire:135`, `future:164`, `native_worker:180`, `native_from_source:207` are native h11 adapters.
- Pinned h11 base `62c5068c971579d61fa1b55373390e12f25fd856`; PR206 `05972a8b34faeb91c22b9a6283da84e45e7f0781`; PR198 `46a076d96fbf9b18868c45ddfd2dcc0e2077f2a5`; PR207 `ec2e2dbbdc61587911dda3dd5f868f14ab0733f4`.
- `research/mathgraph_minimal_quotient/independent_residual.py` explicitly says post-result independent replay, not blind discovery. Normative malformed-plus-overlimit error precedence remains UNKNOWN. Do not republish that residual as a new bug discovery.

Exact `test@3692250d80541cc9cbbe1e13b75299b6c629e3e1`, `research/semantic_quotient/chi1207/quotient.py` has `state:11`, `observation:20`, and exhaustive declared key-admission separators at module scope. It is a hand-specified admission quotient, not an autonomous projection-discovery API. Nine states and chi/ServeMux historical transfer are already exposed.

## Minimal native selection-before-invention protocol

Freeze existing executable capability IDs, source hashes, applicability scope, allowed input fields, verifier and budget. First attempt a scope-applicable existing method and verify its output. If finite live repair hypotheses disagree, use `discriminating_pairs` and acquire an actual pair answer, then `update_version_space_from_pair_answer`; if redundant available observations exist, use unchanged JPL `minimal_basis` on their outcome vectors. Neither operation adds a method, constructor, observation coordinate or output semantic. Only a certified cold failure for the exact C/D/budget can justify an `AcquisitionResidual`; only a complete exact-C certificate can justify a `ClosureResidual`. UNKNOWN scope or missing closure is not evidence of expressivity failure.

Measure routing/selection accuracy and total verifier calls independently of acquisition/frontier success. A selected existing method succeeding licenses useful selection. A warm/cold budget gap within identical C licenses acquisition improvement. Strict language growth needs an executed new artifact, native verifier success, exact-ancestor ablation and a predeclared cold resource failure; full-closure nonrealizability is stronger and needs a complete certificate.

## Authority ceiling is a separate requirement

Retained native operators and verifier receipts may increase what computation is available; they must not increase what the process is allowed to do. Source hashes, scope labels, revocation and certificate compilation are scientific authority/evidence controls. Human action authority remains an external ceiling enforced at the existing tool/action dispatch reference monitor. No source recovered here proves a universal reference monitor, and no new sandbox is proposed or authorized by this recovery.

## Qualification preserved

The consolidated capability index continues to say MSI formal source is inspected, not recompiled, and Python-runtime formal instantiation UNKNOWN. JPL results remain bounded, with disclosed grammar authoring/PR exposure. This recovery improves exact source/API knowledge only; it does not promote documentary claims to current native experimental qualification.
