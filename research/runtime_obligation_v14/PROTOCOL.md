# V14 prospective runtime acquisition of source-author exception obligations — freeze before source inspection

Date: 2026-10-22.
Independent upstream Pallets/Click at exact revision `2247b35ea1c47c727d7a06e51fa280e12a863ff6` (2026-10-04).
Previously uninspected fixed test `tests/test_types/test_IntRange.py`, source candidate module `src/click/types.py`. Paths selected through repository metadata; their contents must not be inspected before THIS protocol lands. Do not substitute another file on failure.

## New mechanism
Unlike V12/V13 compile-time AST templates (failed prospective transfer), instrument the real author's native pytest execution and capture EVERY `pytest.raises` context-manager obligation while tests execute, independent of fixture setup, class structure and local variables.

Frozen instrumentation:
- Load a research pytest plugin via `pytest -p runtime_obligation_plugin`. At pytest_configure wrap `pytest.raises` with a context-manager-protocol delegator. Forward actual expected exception type, `match` and kwargs to unchanged original pytest.raises. Delegate __enter__ and __exit__ preserving pytest behavior.
- Record at raises call site relative test filename and line, required exception class name, native observed raised class (or null), whether original Pytest context accepted the exception, and source file SHA.
- Strictly avoid capturing secrets, payloads or argument values. Never modify upstream test files. A trace of a runtime exception is *documentary execution evidence* of a source-authored requirement, not an independently compiled replay witness or proof of general semantics.
- If no meaningful original source `pytest.raises` obligation observed, return UNKNOWN_NO_RUNTIME_REQUIREMENTS. If plugin perturbs original upstream suite outcomes, fail closed.

## Mutation falsifier, locked
In exact original `src/click/types.py`, locate first `raise BadParameter(...)` AST expression and replace its entire single-line statement with `return None`, preserving all other source bytes. If first candidate is multiline or zero eligible, return UNKNOWN_MUTATION. Run original full test file and the mutated full test file with the same instrumented command. A consequential result requires original suite fully PASS, mutated suite fail, and a formerly matched call-site exception obligation become unmatched or absent (test short circuit reported). If mutation not on exercised path => UNKNOWN_CAUSAL_LINK, no tuning.

## Independent baseline, prospective scoring and cost
The original upstream pytest tests themselves are equal-information conventional baseline; this observational instrument is not better than pytest at detecting failures and cannot claim discovery of new upstream intent. It should capture at least one new class/fixture-backed requirement on first run, and demonstrate causal failure if mutation qualifies. A genuinely new runtime-observation adapter is demonstrated *only* on native original tests without adjusting rules.
Cost charge includes plugin setup, original and mutated native tests, parsing/receipt writes. No automated release or test omission.
No source-author signature beyond pinned Git blob, no universal property inference, no cross-kind Lean proof, no R7.2 or CLC edits.
