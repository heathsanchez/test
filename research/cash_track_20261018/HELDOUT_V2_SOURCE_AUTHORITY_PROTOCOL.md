# Frozen V2 source-authority falsifier (18 Oct 2026)

## Residual observed AFTER original held-out native GREEN
The original source-native run [#39093122857](https://github.com/heathsanchez/test/actions/runs/39093122857) correctly checked original git HEAD identities and fixture bytes, but **git rev-parse HEAD alone does not attest that tracked source files have not been locally modified**. A tainted checkout could retain the original HEAD and pass a modified implementation. The original Go experiment/7-case fixture and its source protocol [3ec172aa](https://github.com/heathsanchez/test/commit/3ec172aa162787d9acc0d7dad3aceeb994dfa6b5) are frozen, unchanged.

## Before coding: exact falsifiers and acceptance
Enhance existing `run_heldout_fern.py` with an independent, generic **source-tree authority check** (not repo-name or function-name special casing beyond the declared injected test path):
1. HEAD SHA exact identity AND `git status --porcelain --untracked-files=all` reports **only one allowlisted untracked fixture**: `internal/api/cashtrack_outage_test.go`; no modified tracked code, no other untracked executable, no deleted source. Fixture bytes must be identical SHA-256 to the frozen independent test file.
2. On both original upstream revisions, qualify this exact state both **before and after native Go tests**, then require original causal 6 PASS / 1 FAIL, author head 7 PASS, and physical no-test 0 named invocations.
3. A physical append of a harmless comment to tracked `internal/api/coverage_verdict.go` MUST be refused while `git rev-parse HEAD` remains unchanged. Restore original bytes and requalify exact clean source.
4. A physical modification of the allowlisted test file MUST be refused while HEAD remains unchanged. Restore exact test bytes and requalify.
5. A second untracked `.go` file MUST be refused even though the pinned test remains present and HEAD unchanged. Remove it and requalify.
6. Physically deleted test must produce zero named-test observations (exit status 0 is not success) and full source remains clean with no extra files.
7. Source SHA mismatch and reference removed remain explicit refusals. Do not weaken native old/head evidence or baselines.
8. No writer privileges, upstream PR comment, actual model inference, hidden benchmark or Kaggle submission. Keep this source-specific bounded trust boundary, not a universal cryptographic attestation.

**Promote only after native original Go package+all adversarial controls run successfully in an independent CI job**. Changes are a bounded **qualification-hardening successor** to original GREEN; not an independent new bug discovery or benchmark-wide false-positive measurement.
