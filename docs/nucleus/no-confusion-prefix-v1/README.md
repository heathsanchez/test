# Independent Nucleus: Nat no-confusion prefix closure

This checkpoint closes a shared valid declaration prefix, not a full Arena test. The current 194-test boundary remains 110 ACCEPT / 60 REJECT / 24 UNKNOWN; frozen 193 remains 108 / 61 / 24. No Arena score gain is claimed.

## Authority and scope

The checker revision is `84c35be307d3c154c6d1bab5dd9b0fdc0a696417`, branch `nucleus-no-confusion-prefix-v1`. Semantic baseline: `0329400bbab751eb6ea645c0a65b30f019e99bfd`; documentation parent: `757365d7a1ca04c474db936cd403a7142e3c981a`.

Qualification: [run 36786656490](https://github.com/heathsanchez/test/actions/runs/36786656490). **SUCCESS**; job `110129560974`; artifact `11130470956`, SHA-256 `5e144422b3a2e3918b09760eaa2bb10b2cb3ca505444d94dc4f03e5080a1d42f`. All 141 Rust tests and all 10 independent-reference engine checks pass; both complete corpora have zero wrong, zero errors and zero changed verdicts. Status: **WARRANTED / REUSABLE for the five dependency-sliced prefixes**. The 24 full-file residuals remain UNKNOWN. Current Arena pin is `4c30c4ac4f14a3a899116beb3ea6131880e79a98`, with current artifact 11090525747 and frozen artifact 10712869614.

The exact candidate has 141 passing Rust tests. The 65,536-step judgment limit, 64 MiB checker thread, and explicit paired-replay launcher stack remain unchanged. This is not a qualification of exports omitted by the downloadable corpus, full Mathlib, instruction ranking, or memory competitiveness.

## What changed

Three compositional ingredients discharge `_private.Init.Prelude.0.noConfusion_of_Nat.aux._f`:

1. On full conversion only, weak-head expose a computed recursor major, then execute only a matching, independently admitted constructor rule of the required arity. Retain all pending applications. Opaque and cheap exposure keep the existing evaluation schedule.
2. Retain a projection of a nonconstructor constant head as a stuck neutral, preserving the declared structure, field index, structure value and pending arguments.
3. Prove equality of stuck projections positively from matching field identities and congruent structure arguments. Preserve binder context, conversion depth and delta policy. A failed congruence premise falls back; it never proves that the projected fields differ. The speculative projection quota is separate from the outer application shortcut quota.

The original zero-branch obligation exposes `Bool.rec ... (Nat.beq Nat.zero Nat.zero)` against `True`. After computed-major reduction, successor-branch comparisons need congruence under stuck projections of a neutral `Nat.rec`. Both occur within the valid prefix.

## Dependency witnesses and independent reference

The slicer in `metatron-kernel/tests/slice_no_confusion.py` preserves source declaration order, whole inductive blocks and all transitive expression/constant dependencies. It retains names and universe records. It is a dependency slice, not a proof of globally minimal syntax.

All five current source files yield slices that change baseline UNKNOWN to candidate ACCEPT: init-prelude, magma-list-pair-n7/n21, and magma-list-deep-n21/n36. The pair-n7 witness is 38,049 bytes, 367 expressions and 17 declaration groups, reduced from a 1,651-record source prefix. Input and slice digests are in `prefixes.json`.

The hosted verifier builds pinned lazylean `68c66fa18c1afe029512b90ecfe0b162c0dcd8fb` and checks every slice with both its lazy abstract machine and substitution engine. Those are two engines within one checker lineage, not two independent checkers. No reference checker is imported into Nucleus or called by its executable.

Source comparison also uses the exact exported Lean kernel `5045d0056413266e57c625dcd7c365b10e377c52`, especially `src/kernel/type_checker.cpp` recursor/projection reduction, and lazylean `src/kam.cpp` and `src/tc.cpp`. Lean itself was source-inspected, not executed in this experiment.

## Causal and safety controls

The computed-major and projection fixtures were observed red against the unchanged baseline before implementation. They cover wrong/free majors, preserved pending applications, field identity, argument inequality and binder identity. A further red control exposed an initial prototype's unintended use of full delta inside a PreferredOnly projection comparison; the final candidate threads the caller's policy and passes the control.

Each of three separate ablations of the final source returns UNKNOWN on the pair-n7 slice: remove computed-major exposure; remove neutral projection retention; remove projection congruence. This shows each ingredient is necessary for this implementation/witness, not that the design is universally minimal.

The protected external projection/recursor negatives remain non-ACCEPT and the current proj-stuck-struct positive remains ACCEPT. Both complete corpora have strict zero wrong, zero non-0/1/2 errors, and no lost decisions. Per-test rows in the qualification artifact preserve timing and input digests.

## Residual and retained failed lineage

All 24 complete-file UNKNOWNs remain. The candidate is a verified dependency for continued closure, not completion of those files. Fresh traces in `frontier/` replace the old first-obstruction locations for this revision.

- All four magma tests now stop in `_private.Init.Prelude.0.Nat.le_of_ble_eq_true.match_1_1`.
- init-prelude now stops in `Nat.div.go.match_1`.
- Four protected bad projection/recursor exports stay at their valid matcher declarations, with differing-neutral-head conversion residuals replacing projection exposure failure.

The first exploratory variant normalized computed majors during cheap exposure and took about 13 seconds on args-before-unfold. Restricting it to full fallback restores the short path; this is scheduling evidence, not an instruction-performance qualification. The prior campaign's rejected shared-budget projection variant remains preserved in residual30-closure-v3 lineage.

An additional unpromoted literal bridge, using an existing predecessor literal expression, advanced pair-n7 beyond its next Nat comparison to `Nat.le.below` admission. It was not included in this candidate or globally qualified. The exploratory patch and logs preserve this observation; do not turn it into a completed Arena verdict. Nat.le.below is an indexed recursive Prop family with two parameters, two indices, two constructors and an explicit recursive hypothesis obligation.

The next smallest experiment is a dependency-sliced test for natural-literal recursor constructor views on this qualified prefix base. Derive the view from exact Nat authority, validate neighboring cases, then independently derive any newly exposed indexed-recursive admission obligations. Retain the four magma files as transfer tests and reclose both full corpora. More generic delta expansion or another label-only residual quotient is not justified by this result.
