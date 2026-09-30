# Nucleus current-round projection qualification

Qualified semantic revision: `c362f35db5a2efe5c629e64c1a3b71e392b473fb`.
Base independent revision: `98f87d9e66fb97987427d68180f51a653d626fdb`.
[Qualification run 36774788433](https://github.com/heathsanchez/test/actions/runs/36774788433).
Artifact: `11125416613`; ZIP SHA-256:
`f5d493aa98d3a8c47da5288ad15daf022c51ca9fd7d23b0d7d67282273a84137`.

## Result

| Corpus | Tests | ACCEPT | REJECT | UNKNOWN | Wrong | Errors | Verdict regressions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Frozen Round 1 | 193 | 103 | 60 | 30 | 0 | 0 | 0 |
| Current v4.34 | 194 | 105 | 59 | 30 | 0 | 0 | 0 |

Only current `perf/proj-stuck-struct` changed: UNKNOWN → ACCEPT, 7.710 ms
in the differential replay, 7.963 ms in the preflight.
The three protected projection/recursor negative controls remain UNKNOWN.
`perf/magma-list-pair-n21` also remains UNKNOWN.

All 128 Rust tests passed. The expensive-body regression was first observed
failing on unchanged base semantics in [red run 36773850880](https://github.com/heathsanchez/test/actions/runs/36773850880).
Controls cover unequal arguments, noninjective fallback, and universe arguments.

## Law and scope

Before unfolding a shared constant-headed application, compare its instantiated
universe arguments and prove every pair of corresponding term arguments
convertible. These positive premises suffice for congruence. A failed premise
does not justify refuting the applications: fall back to existing conversion.

This retains a shared projection function and the original structure application,
allowing `id c = c` to close without unrolling the recursive structure.
The rule is generic; it does not inspect Arena test names or invoke another checker.

Speculation has a shared limit of 32 attempts per outer conversion, depth 16,
and at most 256 reduction-budget units per opaque probe. Exhaustion declines
the optional rule. The depth-only precursor `2519f7b...` is superseded and
unqualified; it must not be used as authority.

## Input pins and evidence

- Current Arena: `4c30c4ac4f14a3a899116beb3ea6131880e79a98`.
- Current input artifact: `leanprover/lean-kernel-arena:11090525747`.
- Frozen input artifact: `leanprover/lean-kernel-arena:10712869614`.
- Exact per-test output: [rows.json](rows.json).
- Summary from the qualified run: [result.json](result.json).

Exit 0 is ACCEPT, 1 REJECT, 2 UNKNOWN; every other code is an error.
The workflow writes evidence before final assertions.

## Remaining work toward #1

1. Qualify the exact current large exports: Init/Std, Mathlib 4.34.1,
   CSLib, Cedar and Navier–Stokes. Record input digests, first residual
   declarations, timeouts and memory.
2. Close semantic residual families while replaying both frozen and current
   corpora with zero wrong answers and no lost decisive verdicts.
3. Measure retired instructions and memory under the Arena harness on
   successfully checked large corpora. This small-suite run earns no ranking claim.
4. Prepare a checker definition pinned to the independent executable only after
   qualification. No upstream Arena submission is made here.

The downloadable corpus omits exports above 10 MB.
There are 30 current residuals: 18 expected ACCEPT and 12 expected REJECT.

| Residual | Expected outcome |
| --- | --- |
| `init-prelude` | ACCEPT |
| `perf/app-lam` | ACCEPT |
| `perf/args-before-unfold` | ACCEPT |
| `perf/church-numerals` | ACCEPT |
| `perf/folded-constant-first` | ACCEPT |
| `perf/folded-constant-last` | ACCEPT |
| `perf/fueled-chain` | ACCEPT |
| `perf/grind-ring-5` | ACCEPT |
| `perf/let-ladder` | ACCEPT |
| `perf/magma-list-deep-n21` | ACCEPT |
| `perf/magma-list-deep-n36` | ACCEPT |
| `perf/magma-list-pair-n21` | ACCEPT |
| `perf/magma-list-pair-n7` | ACCEPT |
| `perf/shared-subterm` | ACCEPT |
| `perf/unroll-versus-evaluate` | ACCEPT |
| `tutorial/082_RBTree.id_spec` | ACCEPT |
| `tutorial/099_ruleK` | ACCEPT |
| `tutorial/112_structEta` | ACCEPT |
| `bugs/nested-unused-param` | REJECT |
| `bugs/proj-of-stuck-prop` | REJECT |
| `bugs/proj-of-subst-prop` | REJECT |
| `bugs/rec-missing-ih` | REJECT |
| `bugs/rec-of-subst-prop` | REJECT |
| `perf/refute-cheap-first` | REJECT |
| `tutorial/100_ruleKbad` | REJECT |
| `tutorial/101_ruleKAcc` | REJECT |
| `tutorial/105_proofIrrelevanceBad` | REJECT |
| `tutorial/111_indexedUnitEta` | REJECT |
| `tutorial/113_indexedStructEta` | REJECT |
| `tutorial/125_accRecNoEta` | REJECT |
