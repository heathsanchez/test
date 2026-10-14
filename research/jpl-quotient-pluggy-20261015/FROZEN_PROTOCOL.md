# Preregistered JPL consequence-quotient test — Python plugin manager

Frozen on 2026-10-15 before reading the target patch, PR title/body, target source and tests.
External repo: `pytest-dev/pluggy`, PR **#759**, selected solely from *filename metadata*:
one changed Python implementation `src/pluggy/_manager.py`, one native test file,
one changelog, recent merged date. Selection not based on known repair or intended behaviour.

- Exact uninspected PR base: `86670ff63cccaaa61a234b3cab0a4f70abfbb66b`.
- Exact uninspected contributor head: `b7ee9181dbe897573d03e8686833f931defd8874`.
- No upstream comments, forks, PRs or writes. Only `heathsanchez/test` branch receives code.
- Head revision is a candidate behaviour source, **not a specification or correctness oracle**.

## Frozen automated method and acceptance

1. **Discover scope automatically.** From the actual Git diff, group Python AST declarations
   (module functions and class methods) by qualified name and compare their bodies
   across exact base/head. Ignore comments/formatting. Select changed functions,
   no manually specified operation/function name, contract, test selector or intervention.
2. **Mine semantic distinction.** Extract changed if/while/conditional/guard-raise predicates,
   names, constant operands, operations, and side-effect boundaries from the original source
   (and revised source for structural delta only). Attempt to learn a minimal observational
   quotient of candidate input/state values preserving measured future outcomes.
3. **Generate probes from code and existing public interfaces.** Allowed generic bounded
   input grammar: None, True/False, -1/0/1/2, empty and short strings, string literals
   found in source, empty/singleton lists/tuples/dicts, and simple object variants
   constructible from importable classes/signatures. No manually written pluggy-specific
   test or class initialization. Maximum 500 generated calls per detected function,
   30 seconds per revision; cap total at 3000 calls. No dependency/network execution
   except native original dependency installation from pinned checkout. Cap process runtime.
4. **Run source-native versions independently.** For each automatically constructed call,
   observe return values, exceptions and a shallow public-state projection on original
   base and contributor head, both separately checked out at pinned exact SHA.
   Raw syntax/AST differences or an independently simulated guard delta alone do **not**
   count as a runtime witness.
5. **Minimize and causal-check.** If observations differ, find least-complex call in
   generated grammar, reproduce in separate source-native fresh process, then compare
   a one-site predicate ablation if machine-localizable. A measured family of probe
   signatures may be quotiented only relative to the declared finite vocabulary.
6. **Strong comparators and negatives.** Report what plain diff + existing CI/tests
   already shows, whether generated witness is absent from original tests, and whether
   witness depends on an invalid invocation. If no valid native witness or observation
   cannot be constructed, output `UNKNOWN` with exact failed step, **not** a success.
7. **Promotion gate.** Warrant only a demonstrably new source-native behavioural
   distinction with reproducible input and evidence, never assume it is a bug or that
   MathGraph outperforms a fully informed competent reviewer. Correctness/spec warrant
   is separate, and autonomous invention of the method-generator (L7) remains UNKNOWN.

## Explicit blinding and scope

The repo/PR is retrospectively merged but previously unused in our reported JPL/Go/YAML/
h11/OPA/IEANTN campaigns. This protocol does **not** make it prospective discovery.
We deliberately do not read PR title/body or implementation until this frozen commit
exists. After freezing, author/test code may be inspected for *diagnostic classification*,
but not to insert per-target assumptions and retrospectively re-label them as autonomous.
No observed win on a conveniently chosen witness may be generalized to arbitrary PRs.

## Primary metric

`NATIVE_SEPARATOR_FROM_GENERIC_SOURCE_MINER` yes/no, and whether the minimal
consequence-preserving quotient and test were generated without a human-supplied
observation interface. Secondary: number of invalid calls, source scope, controls,
total native test results and reproducibility. Comparators receive the same
source, authors' tests and available PR information.
