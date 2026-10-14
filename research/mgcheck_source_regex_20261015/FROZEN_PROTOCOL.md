# Frozen native source-driven regex-obligation genesis — 2026-10-15

## Current objective
Find whether an operation-agnostic method can construct previously absent verification inputs **solely from changes in executable source patterns**, without any author-provided positive test seed, manually named subject operation, or per-repository invocation manifest.

This follows the qualified source-seed-dependent validator test generation and prior Python/C paired interface discovery, and tests a distinct residual: automatically acquiring an executable finite probe grammar from source representations themselves.

## Original frozen externally maintained subjects, chosen from PR metadata WITHOUT reading implementation patches
- Primary: `go-ozzo/ozzo-validation` original PR #208; exact public historical base `dbba76d963f16ad2ea78fd8fb7d36564783cb3c4` → original author head `48423ae967b5ed417f9076caa37e83f24b29dccd`. Metadata title concerns E.164 leading +; PR historical and publicly titled, NOT a genuinely blind bug discovery.
- Transfer: `asaskevich/govalidator` original PR #528; exact public historical base `3dd3875e2b081a20d6eed935913a482fea14ecd0` → author PR head `80fc291b0bc7b293068daf5341c47704fb630d43` (closed unmerged; a contributed proposed fix, NOT current upstream acceptance). Metadata mentions underscores in email domain. NO source diff read before freezing the algorithm or this protocol.

## Frozen single method contract
- Use one unchanged Go-native program for both subject families. Go AST discovers regexp source locations (regexp compilation calls, regex-looking named string constants / declaration expressions, and changed string-literal scopes); no hard-coded repo, PR, function, pattern literal or expected result.
- Operate on actual Git-pinned old/head source snapshots; checks git HEAD and retains file and pattern origins. Exclude original author test files, PR body and fixture examples from input generation.
- **Construct input seeds from original regexp/syntax AST** (literals, alternations, char classes, quantifiers, repeats, anchors) and input refinements (boundary and mutation), not from author tests or manually supplied positive inputs.
- Discover a source-paired regexp whose semantics differ under actual Go `regexp` against the same newly generated strings. Do not trust a patch claim; verify actual old and new native regex compilers and match results.
- Report UNKNOWN rather than assuming intended acceptance, including bad regexes, unmatched source scopes, nonregex changes and unsupported language. A regexp mismatch alone is a behavior difference, NOT automatically a contract violation.
- Real negative controls: remove head/reference regexp → UNKNOWN, substitute wrong pinned source SHA → UNKNOWN, unchanged pattern → no difference. Count every evaluated pair and source-derived input. Source-version hashes, outcome witnesses and method source SHA retained.
- Equal-information comparator uses the same old/head native regexp bytes and reproducible fixed brute-force enumerator. Compare actual finite mismatch yield and execution costs; do not infer superiority absent a real margin. Stronger informed symbolic regex testing can obviously reproduce differences, no unconditional novelty.
- Baseline cannot use hidden PR fix/test text; both approaches see exactly old/head source diffs.

## Discriminators and promotion
- `WARRANTED_BOUNDED_SOURCE_PATTERN_INPUT`: old vs author head actual native Go regexp disagreement on source-AST-derived new input, no original author seed, exact identity, negative controls green.
- `WARRANTED_BOUNDED_TRANSFER`: same unchanged generator succeeds on both distinct external source families.
- `REJECTED_FOR_THIS_FAMILY`: no source-derived matching regex operation or finite witness.
- `UNKNOWN`: source identity, noncompiled regex or missing provenance, invalid comparison.
- **NEVER** promote this to L7 autonomous invention of a *new generator generating operation* because the source-regex selector and synthesis grammar are human written upfront.
- No unapproved production MathGraph Check App changes, GitHub upstream writes, customer installation, calls/outreach, Gmail, Render, merge or deployment.

## Required records
Per family: source pins; symbol/file; actual old/new source pattern; AST-derivation path; generated witness string (print repr/JSON); native source match results; controlled failures; baseline outcome; timing; transition label; limits and relation to known earlier outcomes. Preserve red attempts and unresolved cases. One additional, truly unseen family remains necessary for general-domain method claim after these two fixed known-title bug patches.
