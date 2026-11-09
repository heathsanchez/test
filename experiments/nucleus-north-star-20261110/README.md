# Nucleus North Star: scope of an ACCEPT

**Status: CANDIDATE until native Actions tests run on the exact commit.**

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
