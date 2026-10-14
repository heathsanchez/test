# Frozen unseen-stateful HTTP Range qualification — 2026-10-15

## Objective and declared boundary
Compare a previously unused stateful **HTTP partial-download/resume** source family against independent CodeRabbit review under identical historical source and PR text, and independently test whether MathGraph's source-directed mechanism constructs an executable temporal observer absent from the previous collection/regex grammars. This is a pre-implementation **CANDIDATE**, NOT a verified new operation/L7, NOT an already found defect, NOT a customer win. Do not backfill benchmark positives.

## Immutable target chosen before examining source/patch
- Original publicly open source **lima-vm/lima PR #5229**, “feat(downloader): resume partial downloads via HTTP Range” (from public PR metadata, which exposes intended behavior, not a blind topic). Historical base `f7b1c4f68b90299afc89ffeb47756e5fca590b91`, author head `335f61397af402ef77977a8e0c7a200f923349d1`, 1 commit, 3 changed files, +456/-46, head owned by external contributor, currently **UNMERGED**.
- No code, patch, author test implementation or existing reviewer comments inspected at protocol freeze. Published PR text discloses protocol: persistent `data.part`, `Range` and `If-Range`, 206 append, 200 restart, 416 discard/restart, exclusive cache lock. Not a claim of independently invented requirement.

## Test grammar and epistemic promises
- Independently author a **generic typed HTTP temporal-observation program**, not fixed per-repo literal inputs: states absent/partial/complete and validator identity; actions begin/interrupt/retry/rewrite origin; responses 200,206,416 with valid or invalid ranges; observations completed digest/content, on-disk cache, incomplete partial and error.
- Prespecified contract: when the routine declares a **completed successful download**, the final bytes must equal exactly the canonical HTTP resource representation for the request. A failed run must never promote a truncated/mixed-ETag artifact as complete. Legitimate unsupported HTTP behavior or insufficient authority must be marked UNKNOWN, not bug.
- Separate positive controls: 200 restart and valid 206 resume; protected negative: invalid range/bad validator or interrupted connection may cause failure but not silent acceptance of corrupt final data. Preserve exact 416 behavior in PR statement and baseline.
- *Method genesis* requires the machine to derive and emit a NEW native executable observer-sequence program from source/contract with no analyst pasting target-specific class/method calls after discovering the patch. Human-coded HTTP finite-state tester or explicit handwritten test is **only bounded witness**, NOT autonomous operator-language invention. Physical deletion/negative controls and held-out transfer needed for promotion.
- Strong comparator: CodeRabbit on an **exact base/head copy** with ordinary/default review, same PR text (or neutral title with declared variance). It is not a matched AI coding agent unless equal tool/time budgets verified. Freeze CodeRabbit's output before human diagnosis/classification. Unavailable installer/not-run/expired states are NOT misses. Copilot NOT RUN due plan.

## Execution plan
1. Check the frozen base/head SHAs exist and are source-exact. Create only isolated branches in the owner's Lima fork without modifying master or upstream.
2. Review target original code only **after this protocol commit exists**. Construct the minimal source-independent observer generator; report supplied language/template, actual generated sequence, natively executed original Go before/after and negative controls if possible.
3. Trigger CodeRabbit before showing it any generated counterexamples. Record exact PR SHA and unaltered reviewer output; no upstream comments, fix patches, auto-merges or production deployment.
4. Compare: defect detection, source-to-contract reasoning, executed witness, false positives/inherited defects, reviewer completion and actual cost/time. A zero finding alone does not establish superiority; absent observed source-native violation = UNKNOWN.
5. If native whole-dependency execution is blocked, stop after an independently recorded failure and give runnable precise residual. Keep this distinct from already-warranted cachetools/boltons/SortedDict/OrderedSet, Lima shadowing and ReviewBench #9.

No Gmail, Render, third-party writes, code merges, cloud app changes or paid reviewer access requested.
