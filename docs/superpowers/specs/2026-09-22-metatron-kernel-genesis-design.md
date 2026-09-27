# Metatron Kernel Genesis — Architecture Specification

**Status:** Governing architecture, written before implementation  
**Repository:** `heathsanchez/test`  
**Branch:** `metatron-kernel-genesis-v1`  
**Checker directory:** `metatron-kernel/`  
**Control:** `metalogiclabs/mathgraph-lean-kernel@78c7502bac8a5ba000057b3f083bc0595ac65750` (`flash`)  
**Arena authority:** `leanprover/lean-kernel-arena@f5e1bce6e2dc9c60479b3001b76e01722b403799`  
**Primary optimization metric:** official Arena retired instructions  

## 1. Purpose and claim boundary

This project builds a new Lean Kernel Arena checker from a minimal semantic
substrate. It is not a refactor, translation, or renamed source copy of
`sokonanoda`, MathGraph, nanoda, the official kernel, Tenet, con-leche, or
lean4lean.

The project is allowed to learn from their documented behavior, tests,
failures, and measured residuals. It is not allowed to import their checker
source as its starting tree.

The development law is:

```text
exact Arena residual
  -> least structural capability
  -> smallest deciding experiment
  -> external semantic qualification
  -> shallow executable promotion or rejection
  -> next residual
```

The first qualified claim is deliberately small:

> A direct Rust checker can parse Arena format 3.1.0, preserve sparse and
> out-of-order identifiers, check a minimal intensional dependent-type
> fragment, reject an invalid declaration in that fragment, and decline every
> unsupported or unresolved case without guessing.

No initial claim is made for full Lean, all inductives, termination of
definitional equality, confluence, nested inductives, Mathlib acceptance, or
leaderboard competitiveness.

## 2. Non-negotiable laws

1. Residuals earn generators.
2. Warrant earns relations.
3. Search exhaustion is not semantic refutation.
4. Unsupported syntax, unresolved conversion, and exhausted resource budgets
   produce `UNKNOWN`/Arena exit 2, not accept or reject.
5. A semantic regression rejects an optimization regardless of performance.
6. Semantic structure and implementation-cost selection are separate.
7. Deep evidence is retained; the runtime executes the shallowest qualified
   representation.
8. A promoted capability retains an expansion recipe to trusted operations or
   an exact external qualification certificate.
9. Quotients are allowed only when protected future observations cannot
   distinguish the merged states.
10. The Flash checker remains untouched and is used only as a control.

## 3. External contract

The checker consumes the NDJSON stream produced by `lean4export` format 3.1.0.
It follows the current Arena exit contract:

| Exit | Internal verdict | Meaning |
|---:|---|---|
| 0 | `Accept` | Every declaration is established by the checker. |
| 1 | `Reject` | A supported declaration is semantically invalid. |
| 2 | `Unknown` | The checker lacks evidence or capability to decide. |
| other | `Error` | Malformed input or an internal failure. |

The checker must distinguish malformed export data from a well-formed but
unsupported Lean declaration. Malformed records are errors. Unsupported
semantic features are unknown.

The initial authority corpus is the current upstream Arena layout:

- `good/`: required accepts;
- `bad/`: required rejects;
- `corner-cases/`: either verdict is allowed but a crash is not;
- `other/`: format and synthetic semantic tests;
- real-world and `perf/` corpora for retired-instruction measurement.

No official Arena pull request will be created by this programme.

## 4. Considered architectures

### A. Fork and restructure MathGraph

This would reach broad Arena coverage fastest and inherit the strongest known
performance baseline. It fails the central experiment: representation and
trusted operations would still be inherited before residuals earned them.
This route remains the control, not the candidate.

### B. Verified model-first checker in Lean

This offers the strongest near-term theorem story. Current con-leche evidence
also shows a certification tax, extensional treatment for some nested
inductives, and substantial implementation complexity before Arena-leading
retired instructions become plausible. It is an important independent
authority, not the selected performance architecture.

### C. Residual-grown intensional machine in Rust — selected

This route begins with a tiny typed kernel, an explicit reduction machine, and
tri-state judgments. Each later fast path is a promoted semantic obligation,
not an untracked cache. It gives the best test of the Metatron law while
remaining compatible with the official retired-instruction objective.

## 5. Trusted semantic substrate

The trusted substrate contains only these deciding operations:

```text
parse_record(bytes) -> Record
install(record, Environment) -> Environment | Reject | Unknown
infer(Environment, Context, ExprId) -> Judgment<TypeId>
check(Environment, Context, ExprId, TypeId) -> Judgment<()>
step(Environment, Closure) -> Step
convert(Environment, Context, Value, Value) -> Judgment<()>
level_equal(LevelId, LevelId) -> Judgment<()>
```

`Judgment<T>` is:

```rust
enum Judgment<T> {
    Proven { value: T, warrant: WarrantId },
    Refuted { obstruction: ObstructionId },
    Unknown { residual: ResidualId },
}
```

Only `Proven` may support Arena acceptance. Only a semantic contradiction
inside the implemented fragment may produce `Refuted`. Every incomplete path
returns `Unknown`.

### 5.1 Syntax store

The exporter already provides a directed acyclic expression graph. V0 stores
that graph directly:

- sparse external indexes are mapped explicitly rather than assumed dense;
- forward references allowed by the format are resolved after parsing;
- names, universe levels, expressions, and declarations use distinct ID types;
- expression nodes are immutable after resolution;
- binder names and binder presentation do not enter semantic identity;
- no global hash-consing is introduced before allocation or equality residuals
  demonstrate a need.

This avoids prematurely choosing MathGraph's pointer-identity architecture or
Tenet's host-object layout.

### 5.2 Local context and closures

Expressions retain de Bruijn indices. Evaluation uses explicit closures:

```text
Closure = (ExprId, EnvFrameId)
EnvFrame = Empty | Extend(parent, ValueId)
```

The environment is an immutable frame DAG with a separate observed projection
key. Raw frames execute terms; projection keys identify only the portion a
judgment actually observed. The projection starts conservatively as the full
frame path. Narrower quotient keys must be earned by read-set evidence and a
future-behavior congruence test.

This separates semantic environment structure from the later choice of list,
arena, intern table, or direct-map implementation.

### 5.3 Values and reduction

The evaluator is a small transition machine, not a recursive normalizer:

```text
Machine = (control, environment, continuation)
```

Initial transitions are beta, zeta, constant unfolding under declared
transparency, and rigid exposure of sorts, Pi types, lambdas, applications,
bound variables, and constants. Iota, projections, literals, quotients, eta,
proof irrelevance, and rule K enter only when residuals earn them.

The machine records which transition produced a value. This causal lineage is
diagnostic evidence and supplies expansion recipes for promoted obligations.

### 5.4 Conversion is guarded search

Lean definitional equality must not be implemented as “normalize both sides
and compare.” The architecture assumes neither global normalization nor
confluence.

Conversion is an explicit worklist over judgment states:

```text
(environment authority, context support, lhs, rhs, mode)
```

It tries sound rules whose preconditions are established: syntactic identity,
rigid structural comparison, beta/zeta/delta transitions, and later qualified
iota/projection/proof/eta rules. Visited judgment states prevent accidental
cycles. A frozen search budget is an implementation bound only; exhaustion
returns `Unknown`.

Nonconfluent and nonterminating Arena corner cases therefore cannot turn a
timeout into a guessed semantic answer.

### 5.5 Universe levels

V0 handles zero, successor, maximum, parameters, substitution, and the simple
`imax` identities whose side conditions are syntactically established.
Unresolved `imax` equality returns `Unknown`.

A later universe solver must be admitted by exact Arena residuals. Its required
falsifiers include:

- `imax` right argument provably zero;
- `imax` right argument provably nonzero;
- nested `imax` exposed only after simplification;
- equal universes with different syntax;
- 26-parameter cases that make naive Boolean enumeration exponential;
- out-of-order level indexes.

No single-normal-form shortcut is permitted unless its completeness for the
protected universe language is established.

## 6. Promoted executable capabilities

Repeated successful obligations are represented explicitly:

```text
JudgmentKey = (
  operation,
  environment_authority,
  support_key,
  subject_ids,
  transparency_mode,
  semantic_epoch
)

Capability = {
  key,
  result,
  warrant,
  expansion_recipe,
  dependencies,
  qualification_scope
}
```

The first implementation is an ordinary map of proven judgments. It is not
called an optimization until an ablation shows repeated trusted work was
removed. Direct maps, prehashing, compact tables, and cross-session persistence
are alternative shallow representations selected later by retired
instructions.

Negative conversion results are not cached initially. A negative result can be
invalidated by additional reduction opportunity, transparency, environment
growth, or incomplete search. Negative promotion requires a separately proven
closed-world condition.

## 7. Environment authority and sessions

Every declaration extends an immutable authority chain:

```text
AuthorityId = H(parent authority, declaration identity, semantic policy)
```

The hash is provenance, not semantic proof. A capability is reusable only when
its dependencies are present under a compatible authority.

V0 processes one stream in one session. Cross-session serialization is not
trusted initially. If reparse or rebuild cost becomes a residual, a persisted
capability bank may be admitted only with:

- deterministic encoding;
- exact authority binding;
- dependency closure;
- replay/expansion checks;
- corruption and stale-authority falsifiers.

## 8. Inductives, recursors, and projections

Inductives are not primitive in V0. Encountering an inductive record returns
`Unknown` after the parser has preserved it losslessly.

The development order is residual-driven:

1. nonrecursive single-constructor types;
2. constructor metadata and positivity;
3. simple recursors and iota;
4. primitive projections and their sort checks;
5. recursive and reflexive families;
6. mutual and nested inductives.

For mutual/nested inductives, three candidates must be tested:

- direct intensional rules;
- a translation/model adapter based on lean-inductive-models;
- deliberate `Unknown` if neither is justified or affordable.

The extensional model route may qualify as an adapter but may not silently
change the meaning of the intensional substrate. Its use must be visible in the
warrant and evidence ledger.

## 9. Proof irrelevance, eta, and rule ordering

These mechanisms are admitted independently because their interactions can be
nonconfluent or nonterminating.

- Proof irrelevance requires both compared terms to have an established
  proposition type.
- Function eta requires established function types and guarded extensional
  comparison.
- Structure eta requires qualified constructor/projection metadata.
- Rule K is never inferred from a convenient reduction pattern.
- A reduction rule that resolves one Arena test but changes any established
  good/bad verdict is rejected.

Rule order is treated as evidence-bearing implementation structure. It is
profiled only after semantic qualification.

## 10. Residual protocol and evidence ledger

Every mechanism receives one ledger entry before implementation:

```text
id
date
authority SHAs
baseline verdict/profile
frozen obstruction fixture
residual class
least proposed capability
strongest competing explanation
falsifier
ablation
protected semantic suite
primary performance metric
decision rule
implementation commit
qualification run
retired-instruction consequence
decision: retained | rejected | unknown
```

The repository keeps:

- `metatron-kernel/evidence/ledger.jsonl` as the machine-readable authority;
- `metatron-kernel/evidence/LEDGER.md` as the readable projection;
- frozen fixtures under `metatron-kernel/evidence/residuals/<id>/`;
- qualification summaries under `metatron-kernel/evidence/runs/<id>/`.

A failed or rejected experiment remains in the ledger.

## 11. Incremental qualification ladder

Each rung is monotone in protected behavior, not necessarily in accepted
features.

| Rung | Capability | Required external result |
|---|---|---|
| G0 | Parse metadata and sparse IDs | Parse fixtures; malformed input errors; semantic records decline. |
| G1 | Sorts, axioms, constants, Pi, lambda, application | First supported good accept and paired invalid reject. |
| G2 | Beta/zeta/delta guarded conversion | Tutorial prefix grows with zero regressions. |
| G3 | Exact supported universe equality | Universe fixtures and imax falsifiers pass or decline. |
| G4 | Proof irrelevance and eta, separately | Targeted cases pass; undecidability corner cases do not crash. |
| G5 | Simple inductives, constructors, recursors | Relevant good/bad Arena cases pass. |
| G6 | Projections and recursive/reflexive inductives | Projection and recursor bug corpus passes. |
| G7 | Mutual/nested strategy | Qualified adapter or direct rules; otherwise explicit decline. |
| G8 | Real-world corpora | Incremental Init/Std/CSLib/Cedar/Mathlib acceptance. |

At every rung:

1. freeze the first unhandled or expensive residual;
2. add a failing test that names the semantic break;
3. verify that it fails for the intended reason;
4. implement the least capability;
5. run the entire previously protected suite;
6. retain only zero-regression changes;
7. measure retired instructions against the exact prior checker and Flash;
8. update the ledger and push a checkpoint.

## 12. Performance method

Correctness is lexicographically prior to performance.

The primary performance number is retired instructions measured by the Arena
qualification environment. Native wall time is diagnostic only. Each
performance claim uses:

- exact checker and Arena SHAs;
- identical compiler flags, PGO status, thread count, and input bytes;
- a same-run baseline/candidate comparison;
- at least one causal ablation;
- instruction totals by official performance test and aggregate;
- peak RSS and wall/CPU time as secondary metrics;
- semantic output comparison.

Only measurements with the same metric, cohort, ordered case plan, and
measurement contract are compared numerically. A local proxy may reject an
obvious regression before spending external measurement budget, but it cannot
promote a candidate. A leaderboard number from a different cohort is a
frontier signal, not a denominator for an improvement claim.

A 0.5% improvement is not an architectural result. Changes below 1% aggregate
retired-instruction reduction are normally rejected unless they remove trusted
surface or unlock a separately named mechanism.

## 13. Provenance: new, learned, and excluded

| Element | Status in this checker | Source/evidence relationship |
|---|---|---|
| Tri-state semantic judgments throughout | New organizing architecture | Metatron law plus Arena exit contract. |
| Explicit reduction machine with causal transition lineage | New | Motivated by developmental-checker producer-span experiments; no source import. |
| Authority-scoped promoted judgment capabilities | New composition | Metatron promotion law; MathGraph app-obligation experiments provide the residual. |
| Full-frame execution plus separately earned observed-support keys | New composition | RGRS environment residuals and MSI minimum-sufficient-state law. |
| Guarded relational conversion returning unknown | New selected substrate | Required by Arena undecidability cases and Lean discussion rejecting confluence assumptions. |
| Rust, arenas, IDs, maps, PGO | Ordinary implementation choices | Selected later by measured cost; not semantic novelty. |
| Closure-based evaluation | Learned design family | sokonanoda/MathGraph demonstrate its value; implementation is written afresh. |
| Locally nameless/de Bruijn representation | Established technique | Lean export format, nanoda, con-leche, and Lean literature. |
| Sparse identifier support | External contract requirement | Current Arena sparse-name and out-of-order-level fixtures. |
| Universe `imax` case analysis | Established semantic requirement | Lean kernel behavior, Tenet analysis, Arena bug fixtures, MathGraph census. |
| Runtime model adapter for nested inductives | Possible later adapter | lean-inductive-models/con-leche; explicitly extensional and not the initial substrate. |
| Proof-carrying checker theorem | Not initially claimed | con-leche and lean4lean remain independent authorities. |
| sokonanoda/MathGraph source tree | Excluded as implementation base | Used only for evidence, control measurements, and behavioral comparison. |
| Mechanical patch scripts as product source | Excluded | Direct readable Rust source is mandatory. |

## 14. Evidence pins studied before design

- Metatron design and hardened plan at
  `metalogiclabs/metatron@9f626392f46adf41bb8dcaec91edbbc2f2c1dbc2`.
- Qualified Metatron V0 plus Lean-kernel external residual wedge at
  `metalogiclabs/metatron@3bb0d1cae462014480168a600e1bea58b0d74de4`,
  GitHub Actions run `35612489704`, job `106374830730`: manifest validation,
  placeholder rejection, Lean reference build, 19 Python/differential tests,
  and external-wedge attestation all passed. The wedge establishes the rule
  that only same-plan external PMU measurements promote a candidate; local
  proxies may reject but never promote.
- MathGraph Flash control at
  `metalogiclabs/mathgraph-lean-kernel@78c7502bac8a5ba000057b3f083bc0595ac65750`.
- Current upstream Arena at
  `leanprover/lean-kernel-arena@f5e1bce6e2dc9c60479b3001b76e01722b403799`.
- Historical fork contract at
  `heathsanchez/lean-kernel-arena@192ae0ce847b843e2e0b8ad493f63e1542e32443`.
- sokonanoda control at
  `intgrah/sokonanoda@28c03d0103e004610e4d47a4828965efb2b70af9`.
- con-leche model-based verified checker and its documented certification tax.
- lean-inductive-models translation/model strategy and extensional boundary.
- Tenet's independent rule-oriented checker, universe case analysis, and
  explicit divergences.
- lean4lean's verified-kernel programme and memoization evidence.
- Triskelion verifier quotient laws and developmental controller protocols at
  `heathsanchez/triskelion@9419bade0591576b958f6c693231bd72ca745977`.
- RealityGraph residual/evidence mechanisms at
  `heathsanchez/realitygraph@aea6d005a0997e22831b126b487c919e57831db9`.
- Historical developmental checker and RGRS evidence in `heathsanchez/test`.
- Recent user-supplied Lean Zulip transcript concerning Metalean, extensional
  nested-inductive modelling, universe-solver scaling, intensional
  specification, and nontermination/nonconfluence.

## 15. Rejection conditions

The architecture is falsified or must be revised if:

- broad support requires importing the sokonanoda/MathGraph implementation
  rather than earning mechanisms;
- the explicit machine causes an architectural instruction disadvantage that
  cannot be removed without collapsing back to the inherited evaluator;
- promoted warrants cost more than the obligations they replace and no shallow
  representation passes ablation;
- authority/support keys cannot safely reuse obligations across the workloads
  where recurrence was measured;
- an intensional nested-inductive implementation is infeasible and the
  extensional adapter cannot satisfy the desired specification boundary;
- exact universe equality requires a solver whose cost dominates the target
  workload and no qualified quotient or promotion controls it.

Those outcomes are recorded, not hidden. If an inherited architecture is
already optimal for a subsystem, the ledger will say so and development moves
to the next residual.
