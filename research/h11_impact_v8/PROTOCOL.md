# V8 prospective independent H11 change-impact and mutation-sensitive test selection
Frozen 2026-10-22 before reading H11 source or test contents.

Authoritatively independent project: python-hyper/h11, exact upstream commit 62c5068c971579d61fa1b55373390e12f25fd856.
Closed preselected target h11/_receivebuffer.py. Genuine tests: h11/tests/test_receivebuffer.py (owning), h11/tests/test_headers.py (candidate independent). No replacement sources or tests after first outcome.

Source edit grammar frozen based on exposed previous ItsDangerous: select FIRST AST module-level synchronous function whose last statement is a Return with a nonempty expression and no generator/async/dynamic locals introspection; use exact source-span rewrite RETURN expr => temp assignment + return temp. If ineligible, stop UNKNOWN, never select next module. The extra local is observable through tracing/frames; no universal preservation inference.

Impact admission:
- Correctness: original genuine upstream tests, edited genuine upstream tests, and deliberately incorrect changed-return mutation need authentic native evidence. Mutant must be killed by owning suite; otherwise UNKNOWN.
- Dynamic test-level call/line coverage: independently run coverage collection on each suite (using Python sys.settrace from pytest entry, or coverage.py if installed). If candidate suite never executes any line in edited module while owning suite does, it is *session-level* non-observation only. It is NOT a universal independence theorem or globally authorized skip; source imports/initialization and pytest plugin effects are additional hazards.
- Static and source-identity evidence: pin target and tests, inspect imports and dynamic effects; if any unresolved package initialization or indirect behavior exists, fail-closed UNKNOWN_SKIP rather than claim a proof from zero measured line execution.
- Inject synthetic dependency into candidate test copy (NOT upstream): import target and call changed function or line; selector must rescind any conditional skip. Also detect unauthorized alternate source edit.
- Fair comparison: fully informed conventional coverage-based incremental selector receives same coverage and mutation data and decides same eligibility; baseline TIE unless genuine difference.
- Timings: full versus conditional selected suite only if authorized under declared boundary, otherwise broad runner is correct baseline. Charge original/edited/mutant/test-coverage and checker overhead. No production release authority. Real R7.2/CLC/MathGraph runtime unchanged.

The experimental outcome may be zero safe tests omitted. This is a valid negative; never add ad hoc allowlists or pretend coverage absence proves semantics.
