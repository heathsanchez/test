# Function-proof pairs and closed three-field records

Status: WARRANTED / REUSABLE on the explicit four dependency-slice boundary (2026-10-01). Tested candidate0659bc671a4ef536ed4a096deacd0c61b1ca927e; base13d5c777b9837eaff5d8007f17241682404bff37. Branch nucleus-iff-v1.

## Two bounded laws

1. Singleton Prop with two proposition parameters and two syntactic function fields: infer each field type to inhabit Prop in the successively extended context. Validate constructor result, recursor motive/minor/major, rule field order, metadata, and all RHS lambda annotations. Preserve both domains in projection metadata. This supports Iff and renamed copies without a root-name whitelist. It deliberately does not generalize recursive, indexed, fieldless, or sealed product families.
2. Closed monomorphic nonrecursive record with zero parameters and three data fields: check every field type in the prior environment with empty context at the record's declared nonzero universe. Exclude self-reference and retain constructor/recursor signature, metadata, field order, and rule-annotation checks. This supports Substring.Raw and renamed shape fixtures; dependent fields and larger-universe fields do not acquire authority.

The runtime remains independent. Existing one-field singleton and two-field data/proof paths remain bounded as before. Global judgment budget65536, worker stack64MiB unchanged.

## Test and review lineage

- Initial Iff test commit3285c464181cc7d26affe25f62763daac675bb8b / run 36814607364 failed before reaching the checker because a tool-output truncation marker entered the transferred JSON fixture. This is a harness failure, not semantic evidence.
- Corrected exact fixture atfe71f0a8b76656a78d1faf8b6c28e74459c7c038 / run 36814753278: two intended positive tests fail UNKNOWN vs ACCEPT; six negative groups pass. Exact fixture SHA2569272c4000bc8a7be079dbc1a1c18a2bd0c9c64e9913d533dd63147c7cfd59c27.
- Iff candidate4766009f9fb4eae7e89c0fd898c1b80145ceb069 / run 36814924688 SUCCESS,173 Rust tests, two real Iff slices accepted, four reference-engine accepts, full194/193 unchanged zero wrong/errors/regressions. Artifact11141321292 downloaded ZIP SHA256091989d94230af2f1e49c12a3ceb562d82b415f457eedf14037da4ee690defcc. First fresh trace: magma pair files now stop at Nat.decEq.match_1, distinct-neutral-heads.
- Three-field test commit3cb7ecbcef2e7d3db0879ce239c2bac862a04ad8 / run 36815234962: two intended positive UNKNOWN failures, four negative groups pass.
- Record test fixture preserves the real Substring.Raw block's expression shape but replaces two external field types with Type axioms, to isolate the schema. It is explicitly synthetic; actual dependency slices are checked separately in the qualification workflow.
- Independent read-only review found no Critical or Important issue in either runtime diff. Reviewer did not compile or independently establish corpus results. Minor follow-ups: direct Iff downstream projection/reduction and genuinely dependent-second-field tests; direct closed-record open-field/self-reference tests. Existing code checks these premises, but the new focused tests do not separately isolate them.
- All compilation and test claims refer to GitHub CI. No local Rust SDK was available.

## Evidence boundary

Pinned current194 Arena4c30c4ac4f14a3a899116beb3ea6131880e79a98, artifact11090525747. Frozen193 artifact10712869614. Reference corun1024/lazylean68c66fa18c1afe029512b90ecfe0b162c0dcd8fb, KAM and substitution engines within one checker lineage. Reference agreement supports qualification; independent typing and shape premises grant runtime authority.

Neither this result nor the earlier prefix gains qualifies excluded large corpora or instruction ranking. No official Arena submission or PR was made.

## Final qualification seal

[Run 36815399854](https://github.com/heathsanchez/test/actions/runs/36815399854) SUCCESS, job110219242949. Artifact11141272352,223913 bytes; downloaded ZIP SHA256 bd11c68ea255a2e89ec54c952a67e35a451678d21d6f6bccdff863fbe4c1af2e.

179 Rust tests pass. Four real dependency slices UNKNOWN to ACCEPT: Iff from magma pair-n7/pair-n21, Substring.Raw from Init/grind-ring-5. All eight reference-engine checks accept. Both app-lam controls pass under an 8 MiB launcher stack.

Pinned current194:110 ACCEPT /60 REJECT /24 UNKNOWN.
Frozen193:108 ACCEPT /61 REJECT /24 UNKNOWN.
Zero wrong, errors, regressions, or verdict changes on either corpus. Zero new full-file Arena gains.

All24 first obstructions have been freshly retraced in frontier.json. Pair-n7 and pair-n21 now stop at Nat.decEq.match_1 / definition.value / distinct-neutral-heads. Init and grind-ring-5 now stop at Lean.SourceInfo admission. Other 20 first boundaries agree with the preceding Iff trace.

## Next consequential experiments

Lean.SourceInfo has three nonrecursive constructors with4/3/0 fields, zero parameters, no indices. Its emergence converges with Option and Except: a candidate common family is checked finite sums of constructor telescopes. This is a structural hypothesis, not a qualified general admission law. The five affected positive files are Init, grind-ring-5, deep-n21, deep-n36, and fueled-chain.

Cheapest next experiment: dependency-slice and compare Option, Except and Lean.SourceInfo; derive the minimal common parameter/universe/field and recursor obligations; discriminate malformed field, motive, constructor order and RHS neighbors; verify held-out transfer before broadening runtime authority.

The parallel conversion residual Nat.decEq.match_1 is a dependent Bool matcher despite its Nat namespace. Source inspection shows Bool.casesOn and Eq.refl; no root-cause law is inferred from that syntax alone. Instrument its exact failed equality before changing conversion.

WellFounded remains the first valid-prefix barrier in four negative files. Preserve explicit UNKNOWN until their actual faults acquire positive rejection evidence. Performance, eta, indexed and K-related residuals remain in the fresh frontier.

## Reuse and limits

The reusable convergence is typed constructor-field classification: function syntax does not imply data, and a record's declared result universe alone does not certify its fields. Both new paths establish those premises before installing reduction or projection authority.

The remaining routes proposed in chat—parameterized sums, recursive-field admission, conversion reuse, eta, positive rejection witnesses and differential separators—remain CANDIDATE work. This checkpoint implements the first two bounded admission routes, not closure of all 24.
