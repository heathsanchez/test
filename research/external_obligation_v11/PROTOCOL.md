# V11 independent source-authored executable obligation acquisition — frozen before implementation inspection

2026-10-22. Upstream python-hyper/h11 fixed commit 62c5068c971579d61fa1b55373390e12f25fd856.
Target independent author test: h11/tests/test_headers.py; production target h11/_headers.py. We previously inspected the first ~2KB of this test (several assert equality examples), so this is NOT wholly unopened-source novelty. This experiment must not claim surprise about the assertion family.

## Source authority and question
Question: What observable normalization requirement does the upstream author place on normalize_and_validate?
Instead of injecting an English expected answer, parse the original signed-by-Git-revision source *test* AST for standalone assert nodes matching an expression CALL == literal-expression, where CALL is to exact function normalize_and_validate, and call arguments and expected outputs are entirely ast.literal_eval-compatible. Preserve each unique source span and expected value. Do NOT write expected output values into the compiler. If no eligible assertions, UNKNOWN.

## Safety and witness grammar (precommitted)
Only allow a single call whose sole positional argument is a literal list/tuple containing literal pairs, no kwargs. Only allow expected literal list/tuple of pairs of bytes/str. All inputs/results must use Python basic types, no dynamic code or arbitrary source evaluation. Compile witness by extracting AST literals, loading independently owned h11._headers.normalize_and_validate by original package import, calling it with constructed inputs, and deep comparing output to source expected. A native source author test is executable requirement evidence; it does NOT by itself prove author intended a universal property or independent scientific truth.

## Source-change verification
Pin original upstream source exact commit, test SHA; require generated witness replay on original source.
Make a source-changing implementation mutation from a generic AST operation: within normalize_and_validate, replace first .lower() with .upper() (if absent, UNKNOWN_NOT_ELIGIBLE). Test extracted witnesses and existing native upstream header tests. Record whether both detect a consequential failure. DO NOT adjust after source reveal.
Generate harmless implementation revision as a comment-only change with exact Python AST equality; test witness receipt reuse on this distinct source hash and ensure authenticated source-id changes force requalification. This is weak source preservation, NOT an unanticipated semantic implementation rewrite.

## Fair baseline
Run original upstream header tests on original, comment-only and mutated native code, without relaxing tests. Compare against a conventional AST assertion extractor given exact same upstream text and native tests; if it matches, TIE. Charge all test and checker costs including mutation and extraction; no commercial savings. Existing original MathGraph warrant_resolution may be called in documentary scope only to track source/test/witness-version receipts and revoke on mutation; never grant release or Lean formal source admission.
No upstream PR. R7.2/CLC and production MathGraph untouched. Fail closed rather than source-fit if no assertion or mutation applicability.
