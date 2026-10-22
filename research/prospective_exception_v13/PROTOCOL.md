# V13 prospective exception-obligation transfer — preregistration before source contents

2026-10-22. Project independently maintained by Pallets: itsdangerous at pinned upstream commit 672971d66a2ef9f85151e53283113f33d642dabd.
Frozen *ordered* source-author test family (chosen from directory metadata only):
1 tests/test_itsdangerous/test_serializer.py
2 tests/test_itsdangerous/test_timed.py
3 tests/test_itsdangerous/test_url_safe.py

Do not inspect candidate source until this protocol is committed. Traverse in fixed order and select the FIRST source containing at least one obligation compatible with this EXACT compiler; record all declining diagnostics, and do not fit or change semantics after exposure. Selecting first eligible in frozen list is not hindsight selection.

Frozen grammar transferred from the EXPOSED V12 postexposure one-hop local constructor:
- In top-level test function body, immediately preceding an exact `with pytest.raises(ExceptionClass):` block (no as-clause, no kwargs, one body expression) must be `local = ImportedProjectClass(literal constructor args, literal keyword args)`, with ast.literal_eval-compatible basic literals and imports from `itsdangerous` or `itsdangerous.*`. The protected with-body must be `local.method(literal args, literal kwargs)`.
- Additionally allow a single local variable binding `x = <literal>` between local constructor and the with-block ONLY if body refers to it? NO: rule is exactly immediate predecessor only. No exceptions for fixtures, dynamic values, mutation setup or context binding. A zero-eligible result is UNKNOWN.

Compile full import path, class, constructor, method, args and exception class from upstream AST. No hardcoded expected values, no execution of test source, and no dynamic eval. Run independent witness in clean Python subprocess. Original native upstream test file must pass.
Mutation rule frozen: in the implementation module defining class/method, find the first exact `raise ExpectedException(...)` AST node within the selected method and replace exactly its source statement with `return None`; if no such single-line statement or mutation not causal, declare UNKNOWN_MUTATION, do not seek another method/test. Require both generated witness and actual selected upstream test suite to detect mutation.
- Any expected error class imported from itsdangerous module is admitted only through resolved source import and actual exception subclass check.
- Freeze source hashes; no promise of universal class semantics or author endorsement. If method has complex nested dependencies, mutation likely inapplicable and must fail closed.

Compare with original fully informed pytest and conventional AST+local dataflow extractor given same source. They may TIE. Charge original and mutant native test runs, acquisition and witness work. Use unchanged original MathGraph `resolve_graph` for DOCUMENTARY source/test/native receipts; source/hash or native withdrawal retracts claim. No release permission/Lean cross-kind bridge. R7.2 and CLC unchanged. No upstream PR.
