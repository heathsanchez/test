# Historical source archaeology: Triskelion and MSI

This read-only audit recovered both mandatory historical experiment anchors and directly replayed the actual finite Boolean closure algorithm. The original successful Boolean artifact, and primary artifacts for V54/V161, remain **UNKNOWN** because their bytes were not retrieved. Source assertions and committed result reports are distinguished from independent audit replay below. No repository checkout, source mutation, or external write was performed.

## Inventory and source history

All current remote refs were enumerated from the full parent-supplied clones, rather than only reading default branches: Triskelion has **239 historical remote branches plus symbolic HEAD**, with **1518 reachable commits**; MSI has **340 historical remote branches plus symbolic HEAD**, with **2652 reachable commits**. See `*_remote_refs.tsv`, `*_all_reachable_commits.json`, `*_all_source_changes.txt` (every reachable commit’s changed-file history), and `*_relevant_source_history.json`. This covers history reachable from current refs; deleted unreachable branches and garbage-collected objects are **UNKNOWN**. Relevant source histories were traced with `git log --all -- exact/path`, and pinned extracts are under `source/`.

Initial public clone failed to reach the proxy; the subsequent additional-permission clone blocked and was aborted after 2549 seconds. Local research then used `/workspace/repos/triskelion` and `/workspace/repos/msi`.

## V54 causal O1 → O2

Run [31761530951](https://github.com/heathsanchez/triskelion/actions/runs/31761530951), branch `v54-compounding-ratchet`, head **2dd5f41b6c7cec1004b8deaee4f976dd2a9ed21c**. Exact program: `experiments/METALOGIC_TWO_GENERATION_COMPOUNDING_V54.py` (introduced `626173708326a3e4b5d824947722a962ee103b4f`). The committed progress ledger at Triskelion main **9419bade0591576b958f6c693231bd72ca745977**, `results/PROGRESS_V49_V56_2026-08-14.md:57`, records:

- Before O1, cold one-rewrite search has zero survivors.
- Reusing O1 (`< → <=`) leaves a residual; subsequent one-new-rewrite search discovers O2 (`and → or`).
- Cold FAIL; O1 alone FAIL; O1 then O2 PASS; O1 ablated with O2 retained FAIL.

Program source pins: O1 construction and token-multiset obstruction at lines95–109; fixed discovery after O1 at175; causal execution at199; ablation209; all decisive gates224–235; bounded claim236. This licenses a **fixed-budget discoverability gain and causal compounding** inside a supplied token-emission meta-language. It does not license invention outside all metalanguages. Primary run artifact bytes/digest are **UNKNOWN** in this audit.

**Naming collision:** `results/V54_EXTERNAL_QUOTIENT_REFINEMENT_RESULT.txt` is a distinct homonymous weak/strong verifier experiment. It must not be used as the result of run31761530951.

## V161 structural experiential rescue

Run [32060890023](https://github.com/heathsanchez/triskelion/actions/runs/32060890023), actual run head **5011d53966618c37ec8d28cc43c13db5e2371e7f**. Branch report pin **620e305e4024ba6a818011c7e72a8d138a831875**, `results/V161_AST_ROLE_EXPERIENTIAL_RESCUE_20260818.md:6`, reports artifact `v161-ast-role-experiential-rescue`, SHA256 `8a7d48afbda7262805584e69c0865a035193e9087392f908217a1e0b68d82c4b`. Artifact bytes were not re-fetched.

The frozen protocol (`protocols/V161_AST_ROLE_EXPERIENTIAL_RESCUE.md:18`) supplies two descriptors: `A_APPEND_STACK_LOOP_ITEM` and `B_RETURN_SINGLETON_ARG`. Both prior executable-verified experiences per task must induce the same descriptor. Protected evaluation uses eight heterogeneous-identifier programs per task at a frozen regressed checkpoint. Reported A+B executable hits: neural **8/16**, raw verified memory **8/16**, compiled AST-role map **16/16**, same-budget shuffled map **0/16**.

Actual source functions at the run head: `verify:60`, `source_roles_A:78`, `source_roles_B:91`, `induce_descriptor:96`, `instantiate:114`; admission starts126. This supports **bounded causal reuse of learned structural repair roles**, overcoming identifier variation and regressed neural completion under this protocol. The supplied role vocabulary bounds abstraction. This run does not demonstrate acquisition of a genuinely new O2; its own result identifies that as the next separator.

## Actual 16/256 → 256/256 Boolean closure

Recovered by exact semantic source history, **not by guessing from homonymous V103/V104 constructor branches**. `experiments/V103_OPERATOR_QUOTIENT_COMPRESSION.py` was introduced in `9ffe7fe3fc2e54292fe4293108626386e1ddca5f`. The direct saturation certificate is `experiments/V104_ADVERSARIAL_QUOTIENT_IDENTITY.py`, introduced in **12b437def08a99f3c3a1301e0297c7c6b9ee89f1** and pinned at its corrected version **914703653930e204c2677971fb253f239f0d3764**. The correction removes constant1 from an intentionally incomplete presentation control; the frozen closure protocol is unchanged.

`AFF3:27` is the complete three-variable affine class `c XOR ax*x XOR ay*y XOR az*z`, size16. `close_bool:59` starts with that class and saturates under negation, XOR, and one binary truth-table operator across the finite universe of256 three-input Boolean functions. `G3:129` requires every nonaffine representative to expand to256.

**Independent audit replay passed** the pinned unmodified program. Each of `{1,2,4,7,8,11,13,14}` produces all256 truth tables. The explicit old and expanded closure sets, not only counts, are saved in `BOOLEAN_CLOSURE_CERTIFICATE.json`; the full original-program replay result is `replay/artifacts/v104_quotient_identity/RESULT.json`. The claim is exact relative to this finite extensional Boolean regime and arbitrary finite composition, without a depth horizon. It is not natural-world operator invention or unrestricted developmental completeness.

Original historical successful primary artifact: **UNKNOWN**. The committed result at main, `results/V104_ADVERSARIAL_QUOTIENT_IDENTITY_RESULT_20260815.md:7`, says Actions launches31866781031 and31866821184 acquired no runner (`runner_id=0`, `steps=[]`); successful computation was independently local and not Actions-attested. This audit replay verifies the calculation, not the historical successful artifact's provenance.

## MSI exact developmental regime

MSI main pin **5d448c0ecc82ff3945d009963064ebbb67d2f308**. `CONSEQUENTIAL_CORE_CONTRACTS.md:10` defines shared state **S=(E,H,C,D)**: optional active equivalence E, live residual-relative version space H, executable interaction/constructor language C, optional bounded acquisition policy D. `consequential_core.py:154` implements these plus the carrier. These fields are distinct, so an interface update, language extension, and policy update cannot be substituted for one another.

`ClosureCertificate:74` names interactions, completeness, resource regime, and exact language snapshot. Residuals are tagged (`PairResidual:86`, `ClosureResidual:106`, `AcquisitionResidual:126`); the last binds task, exact C/D snapshots, budget, and certified cold failure. `CLOSURE_RELATIVE_CAPABILITY.md:100` distinguishes interface, reachability, discovery, formability, and policy gains. The finite four-coordinate rewrite witness explicitly shows reachability growth while the raw constructor language is unchanged. Verifier tags in Python are declared fields/checks; independent verifier authentication is an additional runtime obligation.

## MSI exact formal correspondence

Pinned source: `heathsanchez/Minimal-Sufficient-Interface@5d448c0ecc82ff3945d009963064ebbb67d2f308`. Exact extracts are under `source/msi/`. These source proofs were inspected but not recompiled in this audit.

| Source | Exact definition and assumptions | Warranted consequence |
|---|---|---|
| `BehaviouralCongruence.lean:9,25,65` | `ActionMonoid` supplies identity, associativity, and action laws. `BehEq x y := ∀m, obs(act m x)=obs(act m y)`. Competing relation R is invariant and observation-compatible; R need not be an equivalence. | Greatest invariant relation within the observation kernel; quotient action descends, preserves identity/composition, and is unique on representatives. |
| `BehaviouralCongruence.lean:132,136,155,207` | `EqBy B` tests only retained continuations. `Terminal B` says every reachable action respects it. `RefineStep` prepends a genuine separator. `finite_recovery` requires a finite list covering EVERY action, initial empty list, and a genuine refinement whenever nonterminal. | Exact all-futures quotient reached within list length. This is not an unbounded open-world or finite-sampling completeness claim. |
| `TypedBehaviouralCongruence.lean:6,23,39,98` | Explicit small-category laws and a functor-like concrete action; observations indexed by object. Equality under EVERY typed continuation. Competing relation family must be congruent and observation-compatible. | Greatest observation-compatible categorical congruence; quotient maps preserve composition and identity. |
| `DevelopmentalCategory.lean:17,25,30,67,77` | A stage is identity-containing, composition-closed allowed morphisms WITHIN A FIXED ambient category. `Extends` is inclusion. Objects, state spaces, action, and observations remain parameters of that fixed ambient model. | Stage growth refines behavioural identity; a newly allowed continuation separating an old class forces a strict split. A canonical forgetful map runs from the new finer quotient to the old quotient. |
| `ResidualRegimeBridge.lean:19,25,109,163` | A residual is an old `EqBy B` collision separated by a new continuation's observation kernel. Admissible repair retains old distinctions and respects that kernel. `CanDescend` means a function from the current quotient to O realizes `obs(act c x)` on every representative. | Intersection `EqBy(c::B)` is the unique coarsest admissible relation, strictly finer under a residual. New consequence cannot descend before repair and can afterward. This concerns quotient-to-observation descent, not automatically the entire state-transition action. |
| `MinimalRepair.lean:37,48,60` | Abstract `MeetKernel` with commutative, associative, idempotent meet; order is `meet x y=x`. | Meet is the coarsest common refinement, unique by its universal property. Concrete partition equivalence requires a separate representation correspondence. |
| `BlindRecursiveCrossGrammarGenesis.lean:34,60,77` | Three frozen Bool sum/carry programs, exact `decide` enumerations: 8 triples; 64×64×2 six-bit additions; 16×16×2 cut-carry cases. | Semantic agreement of frozen grammar programs, exhaustive six-bit recursive correctness, and deletion equalling two isolated protected blocks. It does not prove unrestricted synthesis, generalized recursion, or a directly stated performance-loss theorem. |

The runtime correspondence still requires concrete evidence that executable actions satisfy these laws, that residuals are verifier-valid, and that promoted coordinates represent these relations. MSI Lean source alone does not prove any arbitrary runtime implementation.
