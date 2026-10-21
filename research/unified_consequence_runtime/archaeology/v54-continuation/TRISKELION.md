# Triskelion native source recovery

Read-only inspection on 2026-10-15. Original repository worktree unchanged; sources were read with `git show`, with extracted copies under this report's `source/triskelion/` directory. No native experiment, clone, upstream action, or model call was executed. Exact per-file SHA256, pins, symbols and extracted paths are in `TRISKELION_INDEX.json`.

## Constructor APIs: version-number collision resolved

The main branch's `experiments/V103_OPERATOR_QUOTIENT_COMPRESSION.py` and `V104_ADVERSARIAL_QUOTIENT_IDENTITY.py` concern finite Boolean/operator quotient laws. Their result files do **not** qualify the constructor branches below.

- V103 native constructor: `origin/v103-verifier-induced-expression-constructor` at `009e0007142467779d182ac29751c61a34645ebf`, `experiments/METALOGIC_V103_VERIFIER_INDUCED_EXPRESSION_CONSTRUCTOR.py`. APIs: `family_candidates(src, allowed)` line 28; `first_success(name,cands)` 31; `main()` 38. Supplied four families at 14; retains families improved on >=2 source-distinct training programs at 44–50, and checks heldout strict closure expansion plus matched wrong-family control at 66–75. Eight train/eight test, cap base 180/expression 240. It selects among supplied builder families, rather than inventing their substrate. `V103_RERUN_20260818.md` is only a trigger/no-protocol-change statement, not a receipt.
- V104 generic constructor: `origin/v104-generic-constructor-synthesis` at `426c54f7c774560e0fabe7213c5ef333b1327c71`, `experiments/METALOGIC_V104_GENERIC_CONSTRUCTOR_SYNTHESIS.py`. APIs: `nodes_for_selector(tree,sel)` 41; `build_expr(builder,names,old=None)` 51; `program_candidates(src,allowed=None,cap=PROGRAM_CAP)` 66; `first_success` 93; `main` 100. Supplied SELECTORS and BUILDERS at 18–27. Training verifier improvement supports programs; source-distinct support and MDL retain up to two at 103–122. Strict heldout gain and same-cardinality wrong-program control at 139–150. This is the strongest recovered finite AST constructor program API.
- V104h scoring hygiene: `origin/v104h-bytecode-safe-generic-constructor-synthesis` at `9ff0e6a393cef499a37f0374ca6315e7849c49b8`, `experiments/METALOGIC_V104H_BYTECODE_SAFE_GENERIC_CONSTRUCTOR_SYNTHESIS.py`. `parse_score` 11, `purge_bytecode` 18, `hardened_full_score(name,text)` 25. It purges target pyc before/after each candidate, disables bytecode writes, runs pytest in subprocess and restores source in `finally`; the main guard replaces V104's scorer at 37–41. Importing the base modules is **not read-only**: they create output directories and may transitively initialize external fixtures. No import was attempted.

V104h's exact local Python dependency closure was recovered at the same hardened pin, not mixed across branch heads: V104H -> V104 -> V102 fresh split -> V100 balanced K -> V99 cross-source dynamic organs -> V98 rich K -> V97 protected dynamic ranking -> V94 dynamic state invariants. All eight source bytes and hashes are indexed/extracted. Historical native constructor result/artifact qualification was not located in this inspection; preserve UNKNOWN. A Boolean V104 result is not substitute evidence.

## V158 explicit retained state

Pin `origin/v158-unified-developmental-runtime` = `ecaea81279000d226562eb11abfe18178ece89bf`. `developmental_runtime/state.py` exposes `EvidenceRef` 31; `DevelopmentalState` 85; `snapshot` 119; `install_capability` 173; `install_law` 195; `install_organ` 206; `install_constructor` 217; `refine_quotient` 230; `refine_scope` 245; `revoke` 262; `set_discovery_policy` 277; `record_obstruction` 290; `active_capabilities` 303; `closure` 315; `verify_event_chain` 341; `replay` 361. Public package exports the subclass from `state_v2.py`, with `set_verifier_config` 43 and richer `active_capabilities` 59.

The event log stores exact state and evidence references. Admission checks `Decision.VERIFIED` plus nonempty verifier/artifact/digest at `state.py:41`; this does not itself inspect artifact bytes or execute a native verifier. `closure` explicitly computes a small requires/provides relation and disclaims domain solving at 315–320. Selftest O1/O2 examples are supplied prerequisites, so their ablation is not empirical constructor discovery.

`developmental_runtime/longitudinal.py:19` is already a native classifier for the intended new frontier. It demands matched apparatus, prospective verified/causal ancestor acquisition, source-distinct native-verified downstream task, downstream undiscoverable without ancestor, discoverable with it, pre-answer frontier shift, and exact restart. Practical advantage remains a separate strongest-comparator/budget/verifier-access predicate at 65–78. It consumes measured facts; it does not establish them.

## V161 executable AST roles

Run source pin `5011d53966618c37ec8d28cc43c13db5e2371e7f`; report branch pin `620e305e4024ba6a818011c7e72a8d138a831875`. `experiments/V161_AST_ROLE_EXPERIENTIAL_RESCUE.py`: `verify(task,names,line)` 60; `source_roles_A(src)` 78; `source_roles_B(src)` 91; `induce_descriptor(task,src,line)` 96; `instantiate(desc,task,names)` 114. Two supplied descriptor schemas: append loop item to stack, and return singleton argument. AST role inference transfers across heterogeneous names, but cannot discover a schema absent from these cases.

`results/V161_AST_ROLE_EXPERIENTIAL_RESCUE_20260818.md` reports run `32060890023`, artifact name `v161-ast-role-experiential-rescue`, reported artifact digest `8a7d48afbda7262805584e69c0865a035193e9087392f908217a1e0b68d82c4b`; compiled 16/16 vs neural/raw 8/16, shuffled 0/16. Qualified capability index correctly says SOURCE_AND_COMMITTED_RUN_REPORT_VERIFIED_PRIMARY_ARTIFACT_UNKNOWN. No artifact or rerun qualification added here.

The report explicitly says at 52–53: do not spend more experiments on identifier renaming. Next separator: prior structure must improve **discovery of a new operator absent from the stored map**, with V54's fixed proposal budget and ancestor ablation. This is a source-authored prospective direction, not an achieved result.

## DevelopmentalIR increasing arity: exact candidate and limit

Strongest recovered staged API is V6 `origin/experiment/developmental-ir-v6-blind-grammar-expansion` at `644f83bb98f772f395b112ca4a6a5a81b3e98c6b`, `experiments/developmental_ir_v6_blind_grammar_expansion.py`:

- `expr_eval_abstract(e,arity)` 44 and `expr_eval_actual(e,args,mask)` 53;
- `synthesize(arity)` 69, `Op` 97, `select_distinct` 107, `build_a4` 120;
- `make_node(op,ch)` 197, `gen_train(task,epoch,depth,...)` 204, `gen_frozen(task)` 212;
- `recover(n)->(arity,table)` 239, native `verify(key,expr)->(bool,digest)` 243;
- `Installed` 249, `language_hash` 257, `evaluate(tasks,keys)` 261, `run_once()` 283.

Its committed summary says PASS_DEVELOPMENTAL_IR_V6_BLIND_GRAMMAR_EXPANSION, all 30 historical gates true; language final counts arity2=2, arity3=10, arity4=12; frozen cost 31654 vs cold 115200, 0.9975 hit rate; language budget 24, 54 admissions, 30 evictions, exact reload. These are committed summary evidence inspected, not freshly reproduced. V1's summary remains PARTIAL: cold/no-promotion lose only ~1.4% of developmental savings, failing E9/E10.

Concrete prospective finite candidate: independently freeze a new D-expression with **arity five**, represent it using unchanged generic `Op`/expression semantics, verify all 32 rows through `verify((5,table),expr)`, build composed tasks with `make_node`, and compare retained-key use with `evaluate`. No new truth-table/verifier algorithm is needed. Do not enumerate `synthesize(5)`: its `2^(2^arity)` arrays are impractical; use the already-supported compositional expression representation. New expression/target identities must be chosen and frozen independently before outputs, with historical identities excluded.

However, frozen `run_once` hardcodes historical 2/3/4 pools, first-encounter dictionaries and 10,000 tasks. Adding task IDs merely extends the same known ecology. A new arity needs an adapter/admission protocol beyond this frozen entrypoint. More decisively, `recover` directly evaluates the supplied expanded target expression; O1 does not make O2 newly discoverable. Thus this is a bounded prospective **schema admission/portability** candidate, not an honest native no-new-algorithm solution to source-distinct V54-style new-operator discovery. Preserve that stronger claim UNKNOWN until a separate prospective discovery harness exists. Do not re-run historical headline and relabel it new power.

## Practical compiler residual

V7 `origin/experiment/developmental-ir-v7-native-backend-reality-check` pin `0b0bc66f908469fdb5b13a9d6cfc4c4fcee20c3a`, `experiments/developmental_ir_v7_native_backend_reality_check.py`: `expr_eval` 55, `load_language` 77, `invocation_stream` 106, `generate_source` 116, `compile_one` 179, `run_one` 184, `run_experiment` 190.

Committed summary remains PARTIAL. All binary checksums agree and source compression survives, but outline text-size N5, hybrid text-size N6 and hybrid runtime N7 fail. Expanded and inline both compile to 905 text bytes, while hybrid is 209731 and outline 236906; median reported runtime expanded 1623 ns, inline 1503 ns, hybrid 22035062 ns, outline 74026870 ns. These historical timing numbers are apparatus-specific, but eliminate a generic native advantage claim. Any practical new candidate must beat strongest expanded/inline compiler output under matched full cost, not merely a symbolic cold cost accounting.

## IKKF portability and routing

V1 `origin/ikkf-v1-portable-capability` = `e9ad29a13c408e21de53ac026cc7c354d979dd50`; `experiments/IKKF_V1_PORTABLE_CAPABILITY.py`: `apply_plan` 82, `run_source` 86, `variant` 96, `repair` 105, `verify_family` 107, `parse_plan` 123, `datum` 137, `pooled_eval` 143, `fresh_eval` 158, `compile_capability(project,seed,practice_names,plan)` 163, `reload_eval` 177. C1/C2 independently compile explicit plans into fresh Qwen3.5-9B River LoRA models, compare decoy/uninstall/reload, and require **both** C compiles pass 0.75 at 214–216. Do not upgrade to independent reproducible portability from one successful compile. Source has module-level clone/training/evaluation side effects; no import was attempted.

V2d `origin/ikkf-v2d-verified-capability-os` = `773a73db5a3d4e143c2c0eed658475a2bdfcfe1d`; `experiments/IKKF_V2D_VERIFIED_CAPABILITY_OS.py`: `transform` 24, `apply` 48, `run(name,src)` 51, `variant` 60, `repaired` 65. Exact external QuixBugs pin `4257f44b0ff1181dedaedee6a447e133219fcebf`. Tests frozen programs possible_change/sieve/subsequences, suffixes100–107, C=CMP@0;BIN@0 and J=CMP@0;CONST@0. It applies both modules and selects iff exactly one passes at 69–80. No learned router, no new capability discovery, and no cheap-routing claim. Precommit preserves V2c route collapse negative (0.5 aggregate, C1.0/J0.0).

The qualified index labels IKKF native qualification NOT RECOVERED. This inspection found source/protocol, not native original receipts; preserve that UNKNOWN and the independent recompilation caveat. These mutation variants start from correct QuixBugs sources, unlike V103/V104's natural buggy-source constructor search.
