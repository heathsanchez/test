# Nucleus North Star: scope of an ACCEPT

**First boundary: WARRANTED_BOUNDED** by [native run #42720315589](https://github.com/heathsanchez/test/actions/runs/42720315589) at commit `fbff72f815a0e93cfe850d921e83698b06a84d86` (3/3 specific checks; library 67 passed, 10 ignored). **Authentic-source extension: CANDIDATE until its separate exact-source run completes.**

The user's North Star is to make our claims more truthful and to keep
unexamined assumptions and false certainty visible. The smallest initial
Nucleus application is to distinguish a checked derivation from a verified
premise and from an independently authorized claim about the world.

## Current objective and falsifier

An independent kernel must accept proofs relative to explicitly admitted
axioms without silently treating those axioms as proven. Falsifier: an
accepted proof that refers to an undeclared proof constant, or a report
promoting the inner ACCEPT into an unconditional claim despite an axiom.

The test fixture has `P : Prop`, `assumedProof : P` as explicit axioms, and
`provedFromAssumption : P := assumedProof`. Its correct inner-kernel verdict
is ACCEPT. Removing `assumedProof`, or substituting the proposition itself
as proof, must remain non-ACCEPT. This is a deliberately *conditional*
acceptance, not a kernel bug. The fixture is a manually constructed minimal
NDJSON input, **not** represented as an original Lean source export.

## What this does and does not establish

- Establishes, if tests pass: native Nucleus handles this specific
  environment-relative proof and rejects the two source mutations from
  admission. No proof rule or Arena verdict has been changed.
- Does not establish: theorem's external intended meaning, truth of `P`,
  absence of other axioms, verified Rust implementation, full Mathlib
  acceptance, official speed, or warrant for any outside action.
- Preserves: all six original standard-budget UNKNOWNs, the selected
  Nucleus baseline, and the distinct MathGraph Cell/MGSO shadow-receipt
  lineage. This is one experiment, not a new authorization product.

## Minimum warranted-claim envelope (design direction, not implemented)

1. **Exact source**: export bytes, Lean/export format, kernel code/flags.
2. **Inner claim**: declared theorem type and inference verdict.
3. **Dependencies**: explicit user axioms and trusted primitives, including
   transitive dependencies; UNKNOWN when not computed.
4. **Independent check**: qualified native run, forged-proof regression,
   and verifiable provenance.
5. **Outer claim**: owner-authorized intended proposition or requirement,
   with a separately checked bridge. Without one: UNKNOWN, even if 1–4 pass.
6. **Revocation**: changes to source/context/assumptions withdraw the old
   claim, unless exact safe transport is proven.

An ACCEPT alone warrants only item 2 within the declared checker and source
boundary. Item 5 cannot be inferred by the proof kernel.

## Next cheapest decisive experiment

After the minimal boundary is green, use a real source-generated export
with the same axiom distinction and the existing provenance pipeline. Only
then consider adding an **opt-in** per-theorem dependency/axiom receipt to
the already separate MGSO observation path. Never let an observational
receipt authorize skipping independent proof checking or change exit codes.

For the active six-UNKNOWN campaign, the highest-return next diagnostic
remains measuring expensive *completed* `Nat.rec`/`Decidable.rec` source
closures with exact pending spine, typing goal and work owner. C84's cheap
repeated BVars alone do not justify caching or change proof acceptance.

## Second bounded experiment: authentic Lean source and transitive assumptions

`AssumptionBoundary.lean` contains three genuine theorems:

- `NorthStar.dependent : P`, using postulated `givenQ : Q` and
  `implication : Q → P`;
- `NorthStar.borrowed : P`, depending on the earlier theorem; and
- `NorthStar.independent : ∀ R : Prop, R → R`, with no user axioms.

The new workflow uses pinned Lean 4.34.1 and lean4export commit
`66f1fb4bc256072069767fce52d39480e4524869`. It records Lean
`#print axioms`, the exact NDJSON export, native Nucleus's exit code,
and a separate Python source inventory. The source inventory follows
the theorem type, proof, referenced theorem bodies, axiom types and
explicit declarations; unrecognized expression constructors, missing
declarations and duplicate JSON keys yield UNKNOWN. An omitted
`givenQ` must remain non-ACCEPT in Nucleus and UNKNOWN in the inventory.

The Python inventory intentionally has a narrower scope than Lean's
own checker and **cannot authenticate** the exporter, source owner,
toolchain or intended proposition. Only matched exact-source CI evidence
could promote this bounded finding. A zero explicit-axiom inventory is
not a general Rust checker soundness theorem or an owner-authorized
external claim. Existing MGSO reuse and the six-original campaign are
unmodified.

The first authentic-source workflow
[#42721978497](https://github.com/heathsanchez/test/actions/runs/42721978497)
compiled the Lean source, generated the NDJSON export, and passed the
Python and native build tests. Its final comparison failed because Lean's
`#print axioms` abbreviated local names while the export used fully
qualified `NorthStar.*` names. This was a display-normalization failure,
not an observed axiom-set discrepancy. An exact RED-then-GREEN regression
was added; the complete corrected CI run remains a separate requirement.

The corrected authentic-source workflow
[#42722601844](https://github.com/heathsanchez/test/actions/runs/42722601844)
passed, with a three-theorem independent inventory that matched Lean's
oracle, Nucleus exit 0 on the authentic source and exit 1 when the
`NorthStar.givenQ` declaration was removed. The preserved report artifact
is [#13720858163](https://github.com/heathsanchez/test/actions/runs/42722601844/artifacts/13720858163).
This is a **bounded exact-source finding**, not a general checker proof.

## Third bounded experiment: proof acceptance is not claim adequacy

`ClaimBoundary.lean` contains the deliberately weaker theorem
`NorthStarClaim.checkedTheorem : ∀ R : Prop, R → R` and a separately
Lean-checked `separation` theorem asserting
`(∀ R : Prop, R → R) ∧ ¬(∀ R : Prop, R)`. The refutation uses the
concrete instantiation `R := False`. The JSON contract explicitly
identifies the stronger `∀ R : Prop, R` as a **synthetic** intended
requirement, not a requirement sourced from a real owner or JPL.

The same pinned Lean source pipeline will independently export only the
weaker declaration for native Nucleus. If native ACCEPT coexists with
Lean's axiom-free separation witness, it demonstrates a precise limit
of the meaning of ACCEPT: a properly checked theorem need not entail
an independently supplied requirement. It is **not** a Nucleus soundness
failure, nor evidence that any authentic user intent has been established.
Any alteration of the synthetic contract must invalidate this example's
existing separation receipt rather than inheriting its status.

The first synthetic-source workflow
[#42723226035](https://github.com/heathsanchez/test/actions/runs/42723226035)
compiled the genuine Lean separation theorem and exported the weaker
proof, but the independent inventory returned UNKNOWN for an unresolved
Lean `True` inductive reference. Its final assessment failed closed.
This is a **supported-subset limitation of the experimental inventory**,
not evidence of a checker soundness failure. The revised pure-implication
source above uses only the previously accepted inventory forms; it was
therefore rerun independently before promotion.

The corrected pure-implication experiment is **WARRANTED within its
synthetic, exact-source boundary** by
[#42723590865](https://github.com/heathsanchez/test/actions/runs/42723590865)
on tested commit `44fbf6e1e8f902640a0e0e91d984eccd9d59045f`.
The pinned Lean compilation checks the two axiom-free declarations,
the source inventory returns BOUNDED with zero explicit axioms,
and native Nucleus returns ACCEPT for the deliberately weaker theorem.
The assessment reports `REFUTED_BY_LEAN_WITNESS` for only the synthetic
stronger contract, and `UNKNOWN` for external owner intent. The complete
18-file [artifact #13721736726](https://github.com/heathsanchez/test/actions/runs/42723590865/artifacts/13721736726)
has SHA256 ZIP digest
`a2181b0da3696e3a147b0a005d4b13488ce51829318d6878063d29cad26b0779`.
All 16 local inventory/claim tests passed on that CI run. The first
failed synthetic-source run remains a recorded UNKNOWN; do not silently
transport its `True`-containing export as a certified inventory.

## Reuse decision

This establishes a reusable *distinction*, not a verified general
claim-adequacy engine: native proof acceptance, exact explicit-axiom
closure, synthetic logical entailment and owner-authorized intent are
separate predicates. Future MGSO receipts may carry these as distinct,
provenance-bound observations, while the Nucleus verdict remains purely
the result of its original independent kernel check. No kernel caching,
proof rules, Arena submission, six-UNKNOWN closure or Mathlib performance
claim is modified or implied here.
