# Nucleus / MGSO claim-boundary consumer gate (synthetic)

**Purpose.** Determine whether an existing historical, exact-byte MGSO
`candidate-match` can coexist with an independently checked non-entailment
witness for a stronger *synthetic* intended proposition, without promoting
an accepted proof into an owner-authorized claim.

**Base.** Independent Nucleus/MGSO authenticated-reuse research branch at
[`53299f3124b714fd068e347f4eb4776b64eb98ce`](https://github.com/heathsanchez/test/commit/53299f3124b714fd068e347f4eb4776b64eb98ce),
qualified by [Actions #41725978408](https://github.com/heathsanchez/test/actions/runs/41725978408).
No Rust source or proof rule is changed by this experiment. Its existing
`--mgso-shadow-dir` and `--mgso-inspect-dir` commands are used unchanged.

**Source.** `ClaimBoundary.lean` defines
`checkedTheorem : ∀ R : Prop, R → R` and
`separation : (∀ R : Prop, R → R) ∧ ¬ (∀ R : Prop, R)`.
`synthetic_claim.json` names the stronger `∀ R : Prop, R` solely as an
artificial contract. Its source/axiom/claim test lineage was first
qualified at C84 research-source commit
[`44fbf6e1`](https://github.com/heathsanchez/test/commit/44fbf6e1e8f902640a0e0e91d984eccd9d59045f)
by [Actions #42723590865](https://github.com/heathsanchez/test/actions/runs/42723590865).
This new branch must independently requalify it against its older MGSO
binary and isolated receipt graph; results never transport by assertion.

**Required independent controls.** The final evaluator must verify:

1. Native Nucleus and native Nucleus with MGSO shadow both ACCEPT identical
   authentic Lean-export bytes, with identical stdout; the graph root exists.
2. A fresh *inspection-only* process returns exit **2**,
   `candidate-match`, `authority=none`, `fresh-check=false`.
3. A byte-mutated export gives `stale`, never a candidate for that root.
4. The manifest remains unchanged by both inspections.
5. Lean compiles `separation` and reports zero axioms for both declarations;
   independent source inventory returns only a **bounded** zero-explicit-axiom
   observation for the checked theorem.
6. The stronger synthetic requirement is **REFUTED**, real owner intent
   remains **UNKNOWN**, and no MGSO receipt or stored label can change either.
7. The Lean separation file is bound to exact SHA256
   `7765dedab06ed7d6fd83b3f8ed895f444a992506b7cab9c5084f8c94a99ff670`;
   even changes outside the exported theorem withdraw the synthetic claim
   warrant until new source qualification. Duplicate JSON contract keys
   fail closed rather than being silently overwritten.

**Safety boundary.** This is a test-only observational consumer gate, not
an integrated authorization/resolver, signature, kernel verification,
warm-skip path, general axiom inventory, six-original ACCEPT or Mathlib claim.
The previous MGSO 208-case parity and source provenance remain as separate
evidence, not silently inherited by a new code revision.

**First CI qualification.** [Run #42726149316](https://github.com/heathsanchez/test/actions/runs/42726149316)
at exact source `503da6ac9c1e6b54823adb25d4effa4372b122c8` SUCCESS:
23 local claim tests, 12 native MGSO process and 13 graph tests, Lean
axiom-free separation, authentic source export, ordinary/shadow ACCEPT,
candidate-match inspection with authority none and stale input mutation.
Artifact [#13722152644](https://github.com/heathsanchez/test/actions/runs/42726149316/artifacts/13722152644)
SHA256 ZIP `4721c1a8e997603f32299bab485431216a829d11fcb3c6af88bd22841a9746f1`.
That run precedes the independent witness-source/duplicate-key hardening;
the latter requires its own fresh qualification.
