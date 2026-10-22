# V12 external exception-obligation acquisition — sealed protocol BEFORE test contents

Independent upstream **pallets/itsdangerous** pinned `672971d66a2ef9f85151e53283113f33d642dabd` (2025-06-14). Previously seen directory metadata only, NOT test_signer.py contents this turn. Fixed source-authority test `tests/test_itsdangerous/test_signer.py`. No replacement target after observing source.

## Previously unseen semantics and frozen extraction grammar
Acquire executable *rejection* obligations from the first 12 AST `with pytest.raises(EXCEPTION_CLASS):` blocks in source order when:
- exactly one context-manager item, exception class a bare Name or dotted Attribute, no `as`, no `match=` or other kwargs;
- the body consists of exactly one expression CALL with arguments made exclusively from `ast.literal_eval` values and an expression callee dotted name path beginning `itsdangerous.`, OR a receiver expression constructed using a call to an imported `itsdangerous` class with entirely literal constructor arguments, followed by one receiver method call with literal args;
- the asserted exception is an `itsdangerous` or builtin exception named by the author, not supplied by the compiler;
- no dynamic AST expression execution; compile only safe allowlisted lookup and literal decoding. Resolve imported aliases through AST imports. If no eligible cases, return `UNKNOWN_NO_ADMISSIBLE_EXCEPTION_OBLIGATIONS` and do NOT choose a different file or loosen grammar after viewing source.
- Do NOT read intended error values from native code, change expected exceptions, use `eval`, or ask a model to paraphrase semantics.

## Native and falsifier
Checkout pinned original repository and run genuine upstream test_signer.py; run each extracted negative witness as separate normal invocation with explicit caught exception type. A passing witness must raise the author-named exception, not any exception.
For semantic countercontrol, mutate exactly one upstream source-defined `raise` targeting the extracted witness's code path only if a safe source mutation of `raise NAME(...)` -> `return None` can be demonstrated, within `src/itsdangerous/signer.py`; predeclare this mutation, else `UNKNOWN_UNQUALIFIED_MUTATION` (not change targets or operators).
The original full native upstream test file must FAIL under the mutation, and at least one acquired witness must fail, to claim consequential detection. Otherwise disclose unsupported.
Compare conventional original upstream pytest detection and parsing a `pytest.raises` block: equal-information baseline TIE unless a measured difference.
Optional separate preserving edit: exact independent source-line comment only, rehash and requalify instead of carrying historical warrant. No semantic preservation claim for comments.

## MathGraph documentary warrant
Use pinned original `metalogiclabs/mathgraph@e48f094fa400c77ab07404645f6e12cfba7ebf45` `resolve_graph`; distinguish source identification, actual author-test identity, extracted error requirement, native witness and permission to act. Withdraw each receipt to UNKNOWN. No formal proof or release authority.
R7.2/CLC and production verifiers unchanged. All actual runs/costs charged, no claimed advantage over equally informed pytest.
