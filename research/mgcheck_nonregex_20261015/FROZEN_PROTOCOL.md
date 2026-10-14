# FROZEN non-regex method acquisition and transfer — 2026-10-15

## Source-selection authority and contamination
This protocol and concrete baseline are fixed BEFORE reading either original implementation diff or original author tests. Only public PR titles/metadata and exact author/base revision identities have been seen; hence these are retrospective, **not blind bug discovery**. The original author provided the intended fixes. Both targets are new, non-regex source-change families not previously used by the MathGraph regex-source generator.

Subject A: `shopspring/decimal` PR #428, historical base `f658fbf1eb94abc869558633a0b9b239300899f4`, exact author head `1fc621e247bcaa551e84a3a49608515ef9cbf13e`. PR title advertises Unicode minus handling in numeric parsing.
Subject B: `Masterminds/semver` PR #303, historical base `8b89c86cb53c57cfd5d07c13de12bc4d78954e99`, exact author head `c9706646b4e12416632860dd87d388c2eed07052`. Title advertises outer-space treatment in version/constraint parsing. Contributor PR closed/unmerged as of metadata inspection, not upstream acceptance.
No external repo edits, App installation, PR comments, messages, outreach, Gmail, Render or production deployment.

## Current method failure and falsifier
Run the unchanged previously qualified `source_regex_probe.go` against exact original old/new sources. Its matching changed-regex method should return `REJECTED_NO_MATCHED_PATTERN_CHANGE` (or typed UNKNOWN), even if static regex patterns elsewhere in a codebase remain. Do not retrofit the old method to hide its failure.

## Single source-native method synthesis attempt
Fix one source-independent GO-AST method *before viewing author patches*. It shall:
1. Discover source functions or methods that take one string argument and return a value+error; find functions whose bodies changed at source-exact base/head. No hard-coded function names or project identifiers.
2. Extract new/removed string and rune literals from the source diff AST, plus visible parser grammar symbols in frozen original code, and construct bounded string input programs using a **fixed, typed, universal** combinator grammar (numeric atoms; separators; whitespace wrappers; literal prefix/suffix substitution; Unicode character witnesses; composition). No author test fixtures or per-target positive examples.
3. Generate and run a Go native test against the **same discovered real package callable** at both original revisions, collecting typed `error/success/value` observations. No hand-authored per-target API wrapper.
4. Freeze program selection as a typed, replayable operation (e.g. `Wrap(base, originalLiteral)`), minimal differing input and exact source + function identity. Run same input on author-head. No semantic correctness promotion merely because outputs differ.
5. Real causal negatives: remove generated test and verify no named native test observation; remove original source reference → UNKNOWN; wrong declared SHA → UNKNOWN. Retain true CI red setup failures and avoid treating no tests as PASS.
6. Compare to an equally-informed conventional differential tester with the same exact source and input grammar (must not claim a win if it can find the same). Runtime and candidate costs separately documented. Tests against more capable systems not performed.
7. Exactly the SAME generic generator source and frozen budget runs on both subject A and B without any repository/function-specific additions after inspecting patches. If one fails, preserve failure rather than tailoring it.

## Promotion criteria
- `WARRANTED_BOUNDED_NONREGEX_NATIVE_DIVERGENCE`: own Go-generated test executes against unchanged original application function and produces differing native observed behavior (old versus author head) on a NEW source-derived input; exact-pinned revisions, independent Go compilations, executed negatives.
- `TRANSFER`: identical generator works on both separately maintained source families.
- `REJECTED`: unchanged old regex method unexpectedly succeeds, or no genuine new test, or outputs tie.
- `UNKNOWN`: no reliable callable, source identity, environment dependency, generated test execution, or strong semantic oracle.
- **L7 autonomous invention of a new generator meta-language remains UNKNOWN** even if method succeeds, because its combinators and adaptive search substrate are human-authored. A newly assembled program *within* a fixed grammar is not a self-invented language.
- No invented reviewer superiority or external customer adoption.

## Scope limits
Old/new source diff is available to both contestant and baseline, but author PR test additions remain excluded from input synthesis. A known PR title is not an unbiased blind success. Source-grammar inference cannot establish English requirements. Any semver/decimal source-level change should not be credited to regex method. Stop at two families; do not manufacture a longer experiment list. Preserve failed setup and test failures exactly.
