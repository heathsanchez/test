# Result — OPA #9216, MathGraph Check v0 vs original source-native Go/WebAssembly

**14 October 2026 NZDT · Final: NATIVE_REPRODUCTION_PASS / MATHGRAPH_SPECIFIC_FINDING_FAIL**

[Frozen protocol, committed before original patch inspection](./opa_9216/FROZEN_PROTOCOL.md). [Complete single GitHub Actions run #38548773394](https://github.com/heathsanchez/test/actions/runs/38548773394): BOTH read-only owned jobs SUCCESS at source `96b56ef50bc37517df7ad989287f06657986dee9`.

Unchanged actual MathGraph Check shared `analysis.mjs` (Git blob `a21d34622f3b283db989462aa4a5a8ef00bcae77`) ingested original [OPA PR #9216](https://github.com/open-policy-agent/opa/pull/9216), 6 changed files, exact author head `d231b0381efd880597db736efdd74e6681000b54`, upstream original green GitHub CI. It returned **BEHAVIORAL_SCOPE_UNKNOWN**, `neutral`, and 0/2 source-specific descriptions: no identification of `strings.replace_n` topdown/Wasm mismatch or empty-key timeout. It safely avoided false authorization; this was an owned **shadow** evaluation, not an installation or Check POST on outside OPA.

Actual untouched original OPA revisions independently compiled and exercised from code: predecessor `37030a09d6088821a473f486fd75dd81ef394b74` topdown `Y`, Wasm `anotherX` for the original overlapping pattern; author fixed revision topdown and Wasm both `Y`. Old Wasm empty-key input timed out after **25 seconds**, fixed revision both returned `XaXbX`. Eight original executable CLI arms observed. Timeout is bounded, not universal proof of nontermination. **Upstream author wrote the fix/test case; MathGraph did not.**

Evidence: [Product ZIP #11885193342](https://github.com/heathsanchez/test/actions/runs/38548773394/artifacts/11885193342) sha256 `c64403c4b7cafdb7784fb6238c462293e9bbf63776c633ef4a0fb8ae0a3e5e3d`; [Native ZIP #11885458097](https://github.com/heathsanchez/test/actions/runs/38548773394/artifacts/11885458097) sha256 `227bf3dd3bf6a32fce6dbfe272305d02ac06af1de9fa2d878715eb419b9118e3`. Both independently downloaded and parsed.

Strong-baseline caveat: the author's PR body **already disclosed both issues**; a conventional reviewer with the same public PR body/diff/tests could identify them. No independent human reviewer or measured human time/cost, thus no quantified economic advantage/disadvantage. The product's actual analyzer ignored title/body and source execution. This tests a historical already-solved PR, not prospective bug discovery.

Initial run #38548652467 had original-native job PASS, but the product job failed on an apparatus-only assumption that a contributor's PR head repository must equal upstream. Corrected fork identity check without changing target or scoring, final run #38548773394 both jobs SUCCESS.

**Next scientific/product consequence:** do NOT fit an OPA-specific rule and call it held-out. Candidate source-native general operator must generate an actual cross-implementation witness from original source/test/statement under exact authority, with explicit UNKNOWN and action scope; pre-freeze second outside-source family, compare fully informed conventional/SLSA/SCITT verification, run ablation/restart/withdrawal, and reject general advantage if no out-of-domain benefit.

No external messages, PR comments, app installs, third-party writes, Gmail, Render, grants submitted, or merges. [ROS checkpoint](https://app.notion.com/p/3f93e523d7ab8151a4eef5e72f3aee0d).
