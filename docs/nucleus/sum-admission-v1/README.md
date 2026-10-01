# Nucleus executable sum admission

This campaign repairs the preceding diagnostic-only experiment's objective:
qualification must require new local semantic closure, while preserving every
established correct Arena decision. Normal/diagnostic parity is separate from
baseline/candidate monotonicity. UNKNOWN is allowed to become a correct verdict.

## Derived laws

1. Closed sums: one monomorphic nonzero-sort inductive, two or three constructors,
   at most four fields per constructor, no parameters, indices, nesting,
   recursion, reflexivity or unsafe declarations. Every constructor, minor and
   rule field type checks at the inductive universe in the prior environment
   and empty local context. Existing conversion may identify field annotations.
   The motivating equality is `optParam Bool false` convertible to `Bool`.
2. Parameter sums: one inductive with one or two distinct Type-universe
   parameters and two constructors, each with zero or one field selecting one
   type parameter. Result universe is the parameter universe or their maximum.
   Constructor parameters/results, recursor telescopes, and every rule binder
   and field order are checked explicitly.

Both laws reuse existing signature promotion and certified recursor reduction.
Neither installs projections or structure eta. Both run only after an existing
admission path returns UNKNOWN. Unknown or failed premises grant no authority.

## Required observations

- Five real dependency slices: SourceInfo in init-prelude and grind-ring-5;
  Option in magma-list-deep-n21 and n36; Except in fueled-chain.
- Rename controls and malformed annotation, metadata, universe and field checks.
- Direct recursor execution for all three SourceInfo constructors, both Option
  constructors and both Except constructors.
- Pinned lazylean KAM and substitution engines: two engines, one independent
  implementation lineage, never used as a Nucleus runtime backstop.
- Removing SourceInfo field conversion must restore UNKNOWN. Disabling the
  parameter-sum adapter must restore UNKNOWN on its runtime witnesses.
- Full 194-current / 193-frozen reclosure with no wrong/error/regression and
  exact normal/diagnostic parity. Keep local gains separate from whole-file gains.

## Preserved failed lineage

- `0e24b66edb24adad3245e054195c692e48ece71f`, run 36825756945:
  intended RED. Two SourceInfo prefixes and rename returned UNKNOWN;
  malformed controls passed.
- `1cbb966fa60acebb794ab5b50fa93937f8fefb21`, run 36826408946:
  dispatch regression. The new rule preempted established binary-enum checks,
  changing known REJECTs to UNKNOWN. Three existing unit assertions failed.
  `aa8ea8e842c870fe019db66062acf0ccf0c1b23f` restricts new admission to
  existing UNKNOWN and preserves primitive installation.
- `e3ec5a02fe34b2bfaac134250f68158c1b781f43`, run 36826793410:
  intended RED. Three Option/Except prefixes and renamed Option returned
  UNKNOWN; malformed controls passed.
- `cddfa1f9b1b5a94ba95b156f9f0c251f205912ea`, run 36827310238:
  all three parameter prefixes, renames, and malformed controls passed. One
  newly generated iota witness was rejected because its Type-valued motive
  was instantiated at universe one instead of two. The test generator is
  corrected at `113e3155f0f75c56a269d77aa62914931a3b7b63`; checker code is
  unchanged. This is a fixture failure, not a reason to weaken conversion.

## Closed-sum qualification

`aa8ea8e842c870fe019db66062acf0ccf0c1b23f`, run **36826562901 SUCCESS**,
artifact **11145577862**, downloaded ZIP SHA-256
`1c176316497bc1deec26a26758ce7f3a3bfc90cb8c03726d5d079df5aa432673`.

179 normal Rust tests, 181 diagnostic Rust tests and eight Python tests pass.
Both SourceInfo slices change UNKNOWN to ACCEPT. Three generated iota witnesses
pass Nucleus and both pinned reference engines. The conversion removal returns
UNKNOWN; restoration returns ACCEPT. All 387 corpus verdicts remain unchanged:
current 110A/60R/24U and frozen 108A/61R/24U, zero wrong/errors/regressions.
Both affected whole files next stop at `Lean.Name` inductive admission.

## Combined qualification

Candidate **`113e3155f0f75c56a269d77aa62914931a3b7b63`**, branch
`nucleus-parameter-sums-v1`, [run 36827637235](https://github.com/heathsanchez/test/actions/runs/36827637235)
**SUCCESS**, job `110256796584`. Artifact **11145474972**, 539741 bytes,
downloaded ZIP SHA-256
`301097bcbf9d189e6a51bbf6020c5b9cb3e1daee9d5e03705c29d6b803c418b6`.

- 179 normal / 181 diagnostic Rust tests and 15 Python tests pass.
- All five real slices change UNKNOWN to ACCEPT. Renaming retains acceptance.
- All seven generated recursor witnesses ACCEPT, with 24 successful reference
  executions over the five slices and seven witnesses (two engines, one lineage).
- Conversion ablation restores SourceInfo UNKNOWN; restoring conversion gives
  ACCEPT. Disabling parameter-sum admission restores UNKNOWN for all four
  Option/Except witnesses; restoring it gives ACCEPT.
- Current 194: **110 ACCEPT / 60 REJECT / 24 UNKNOWN**.
- Frozen 193: **108 ACCEPT / 61 REJECT / 24 UNKNOWN**.
- **Zero whole-file gains, wrong verdicts, errors, or regressions.** Normal and
  diagnostic verdicts agree on all 387 cases. Both 8 MiB launcher controls pass.

The new laws are warranted reusable capabilities within their stated bounds.
They are executed in the checker and have measured downstream effects. They
do not, by themselves, complete any of these five whole exports.

| Affected files | Closed admission | Next measured blocker |
| --- | --- | --- |
| init-prelude; perf/grind-ring-5 | Lean.SourceInfo | Lean.Name |
| perf/magma-list-deep-n21; n36 | Option | GetElem? |
| perf/fueled-chain | Except | Functor |

Next operation: compare GetElem? and Functor against the already qualified
record/telescope capabilities. Both are safe nonrecursive single-constructor
records, but their parameter/universe/dependent-field obligations differ:
GetElem? has four parameters, three universe parameters and three fields;
Functor has one parameter, two universe parameters and two fields. Their shared
admission is a candidate, not a warrant inferred from shape. Lean.Name has three
constructors with recursion and needs a separately checked recursive law.
Retain the other twelve typed conversion and seven admission obligations.

`result.json` and `rows.json` preserve exact reclosure; `prefixes.json` preserves
source hashes and independent checks; `ablation-iota.json` preserves executed
causality; `frontier-delta.json` records all 24 former residuals without conflating
an advanced boundary with a whole-file closure. Failed candidate commits and
test-fixture lineage above remain part of the report.

## Pins and limitations

Semantic baseline: `0659bc671a4ef536ed4a096deacd0c61b1ca927e`.
Diagnostic parent: `b7d7baebf8485122fe02afe2e8d910189551cfe2`.
Current-round Arena source: `4c30c4ac4f14a3a899116beb3ea6131880e79a98`,
test artifact `11090525747`; frozen Round 1 artifact `10712869614`.
Reference: `corun1024/lazylean@68c66fa18c1afe029512b90ecfe0b162c0dcd8fb`.
Judgment budget 65536, checker worker stack 64 MiB; app-lam launcher controls
also run at 8 MiB. Rust execution and reference qualification occur in hosted
CI; no local Rust execution is claimed.

No result here qualifies the excluded >10 MB corpora, Mathlib, or Arena
instruction ranking. No official Arena submission is made by this campaign.
