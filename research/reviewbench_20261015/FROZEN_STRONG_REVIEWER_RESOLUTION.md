# Strong-reviewer-informed complete bounded repair: preregistered continuation, 15 Oct 2026

**CANDIDATE / NOT TESTED at freeze.** Previous exact [GitHub Actions #38634398935](https://github.com/heathsanchez/test/actions/runs/38634398935) qualified a genuine negative for the earlier four-case source-identity patch: original old tests repaired 4/4, but two original published Claude Sonnet 4.6 true-positive pagination residuals remained. Archived ZIP #11926569574 SHA256 `47a9a7dd6ba7d2a9bbdca3e4ac3ed537c327e189a2142083bb6c83e4fbe5076c`, report JSON SHA256 `29deed6cde4d72a56a7323d96e80540810589456e190beec2b19f7e9d37a0f3a`. The first native result and the failed adequacy claim are separate, immutable, and must not be rewritten retroactively.

## Goal and baseline

Use the explicit published ReviewBench strong-model findings as **known obligations**, not new discoveries. The model already found (A) commit identity vs clocks, (B) >30 commit pagination, (C) >30 review pagination, (D) premature dismissal/invalid review states, and an additional broader PR flow error. The new test must NOT claim to cover all findings by solving only these listed cases. The strong model is NOT run again, the evaluation is retrospective, not equal-information blinded and cost advantage UNKNOWN.

## One source-minimal patch hypothesis

Replace listing PR commits with an authoritative **single PR-head SHA** REST query at the exact PR number. Enumerate reviews with an explicit bounded paginated REST request (normal GitHub page size or larger), comparing `review.commit_id` to `pull.head.sha`, accepting only submitted active Copilot review states, not DISMISSED/PENDING. Fail closed on missing head SHA or any network/API error, and do not assert universal GitHub API pagination correctness beyond declared max-page bound.

This is a HUMAN-DESIGNED patch, derived from published original PR contract and baseline findings, not an L7 generator. The first qualified timestamp→SHA patch remains historical prior evidence, not copied as final authority.

## Independent native gate

1. Source `review-bench/k1LoW_gh-copilot-review@f98281938e63acd1d2df9b89d6af98dcf58c9fa8` and prior test fixtures at exact pins. Native old source RED on SHA/clock and two paginated scenarios.
2. Prior four-case identity test unchanged except mocking the independently available single PR-head REST source and proper review state in fixtures. Existing first-page control remains.
3. After the NEW candidate patch on ephemeral original code, require PASS on all four identity cases, two >30 pagination cases, first-page control and explicit dismissed-review/missing-head negative controls.
4. Physically restore original source bytes, rerun identity and paginated tests: original failures must reappear. Restore/remove test fixtures, record per-command logs, exact source/patch hashes and complete decision.
5. Run original native package tests where feasible. If native full-suite fails due environment/toolchain, record typed UNKNOWN and do not claim full-package qualification.
6. Compare the outcome only to the strong **published** review baseline, which was already aware of the defects. Differentiate executable resolution and coverage, NOT detection superiority. Record source-native execution cost, number of REST calls and remaining known context-sensitive issues separately.
7. Accept only `WARRANTED_BOUNDED_REPAIR_FOR_DECLARED_CONTROLS`, with `safe_to_merge=UNKNOWN`. Do not update live App, upstream source, PR comments, branch protection or deploy. No Gmail, Render or external outreach.

## Strong comparator limitation

A truly matched model comparison would require running a capable coding reviewer with the same source access, test tools, time and budget on prospectively held-out cases. That was not run, and this experiment must not claim it. The official benchmark Golden file is never fed into the actual adapter for leaderboard scoring.
