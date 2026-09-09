# Open Development — bounded executable core v1

This is a small implementation of the existing MSI/UVRM programme, not a new universal theorem or a replacement for the production Lean kernel. It reuses the V30 developmental runtime for finite commitment routing and probe synthesis. The new wrapper supplies durable evidence, scoped admission, exact dependency revocation, and a single object/method development entry point.

## Native mathematical core

`lean/Kernel.lean` and `lean/Completeness.lean` are exact copies from `heathsanchez/Minimal-Sufficient-Interface` commit `5d448c0ecc82ff3945d009963064ebbb67d2f308`. They establish the meet law and protected-family stopping theorem. `lean/Core.lean` adds typed observation/capability/policy changes and an explicit soundness obligation for a domain checker. No theorem says arbitrary proposals are true. The trusted authority is the actual verifier, not the model.

## Operational boundary

`Developer.run(Obligation) -> Result` reads the active crystal, assesses the obligation, proposes a repair only for a certified residual, checks it twice, attaches it, retains it, and reassesses. The result is a verified/refuted/obstruction/unknown verdict with evidence, a state ID, and any retained capability IDs. `UNKNOWN` is never promoted to impossibility. The same entry point accepts object and method obligations; policy revision does not silently change observational identity.

Every adapter now declares one `IRContract`: nominal obligation, program, result, semantic, observation, and certificate types. Every executable capability separately carries a `CapabilityContract` binding its input type, output type, semantics, and certificate type. Untyped adapters and executable repairs fail closed before development. These are runtime-enforced typed identities and provenance boundaries, not a proof that arbitrary domain encodings preserve semantics; each adapter's verifier still owns that proof obligation.

The Lean `Realization` contract makes that remaining obligation explicit as a commuting observation square between domain execution and IR execution. The Mathlib-backed proof-program gate proves generic interpreter soundness and checks the concrete retained interval-program identities and nonnegativity theorems for O2 and O3. This closes the semantics boundary for the qualified proof-program realization only; it is not a theorem about every future adapter.

`EvidenceStore` retains an append-only SQLite event history and derives the active state. Revocation removes dependent capabilities, but leaves the history intact. Admission identity binds both the content-addressed repair and exact verifier identity: stale evidence is not reused, while an unchanged repair can be explicitly requalified under a new authority. Hash chaining detects damage; it does not protect against a malicious full-history rewrite. Use a single writer and externally attest the ledger for stronger integrity. The adapter is a trusted boundary: its checker must independently justify its claimed contract. A matching certificate label alone is not proof.

## First domain adapter

`finite.py` uses the existing V30 `DevelopmentalRuntime`, `SynthesisRegistry`, and exact finite experiment-policy router. The supplied JSON specifies the entire model, initial and candidate observations, and lawful actions. The actual world is used only after routing. A retained probe is reusable across tasks in the same model and verifier identity.

The default CLI requires Lean. `lean_gate.py` generates a concrete finite certificate and checks strict observational refinement and admission using the pinned Lean core. The finite table is an assumption; Lean does not certify its origin, the optimality of the Python search, or an unrestricted development claim. Use `--finite-only` explicitly for model-relative tests without Lean. Capabilities admitted under different verifier identities are not interchangeable.

## Run

From the repository root:

```bash
python -m unittest discover -s open_development/tests -v
bash open_development/lean/check.sh
python -m open_development.cli --state /tmp/developer.sqlite run --spec open_development/examples/finite.json --task first --world 1 --budget 1
python -m open_development.cli --state /tmp/developer.sqlite run --spec open_development/examples/finite.json --task second --world 1 --budget 0
python -m open_development.cli --state /tmp/developer.sqlite status
```

The same commands with `--finite-only` use the explicit finite-model checker. `revoke ID --reason TEXT` removes a retained capability and its descendants. The CLI state defaults to `.open-development/state.sqlite`; do not commit this database.

## Claim boundary and next qualification

The first qualification tests exact finite refinement, a real Lean gate, retained reuse, restart, cold budget, exact ablation, and rejection of unbound/replay-mismatched evidence. The method-policy test is a deterministic contract fixture, not a scientific K4 result. No model calls, arbitrary code execution, unrestricted grammar invention, independent Lean4Lean trust, or universal cross-domain adequacy are claimed. Method improvements require prospective matched controls under `METHOD.md`; a successful task is not automatically a causal retained capability.

## Proof-procedure adapter

`ProofProcedureAdapter` routes rational-polynomial nonnegativity obligations through the same `Developer.run` transition. Procedures emit inert certificate data. An independent exact-rational replay checker reconstructs the denoted polynomial and checks the constructor's domain side conditions before admission. The qualification acquires square completion, restarts, shows that it is inadequate for a held-out interval obligation, and then acquires affine-factor decomposition. Fixed-language, sham-language, forgery, restart, and exact-removal controls are included.

This establishes a second semantic adapter and bounded self-application to proof procedures. The constructor grammar and obligations remain supplied and finite. The exact replay checker establishes the adapter contract; the prior procedure-repair qualification separately Lean-checks the generic mathematical rules. It does not establish unrestricted constructor discovery or a causal advantage for residual-rich selection when only one candidate succeeds.

`ProofCompositionAdapter` adds the stronger multi-generation capability-growth control. The first obligation justifies and retains a binary product constructor and a ray-specific program assembled over primitive certificate nodes. After restart, that constructor builds a distinct interval program; the program is independently replayed, retained with an explicit constructor dependency, and then reused after another restart on an unlisted third obligation at zero acquisition budget. Removing the ancestor constructor transitively removes both programs and restores the failure. This is bounded constructor-enabled acquisition and program reuse, not invention of the primitive grammar.
