# Exposed V3 diagnostic recovery for native authority V4

All seven V3 refusals are now exposed development diagnostics. No extension, native rerun, new source query, task search, or eligibility promotion was performed. The original result remains seven screened, zero eligible, six environment UNKNOWNs and one contract UNKNOWN, with zero native and collection calls.

The retained audit reported 12,915 substantive checks passing, then disclosed eight Git index cache refreshes and a raw stderr redirection incident. Its audit obstruction and G6 UNKNOWN remain unchanged. Pre-audit index bytes were never captured and are not reconstructed.

Inventory records all source bytes, including intentionally malformed parser input. Environment inference derives interpreter/dependency constraints without treating every `.py` file as executable metadata. Native authority must preserve the actual suite, doctests, conftests, imports, plugins, generated inputs, configuration and command semantics. Malformed executable imports must fail.

| Case | Repository and exact base commit | Original obstruction |
| --- | --- | --- |
| case-000 | `davidhalter/parso@1e4076f9d9ac57052151193af5cb2d72f8b1113b` | `UNKNOWN_SOURCE_PARSER` |
| case-001 | `grantjenks/python-sortedcontainers@13d30bc654eb9e6be092282ca502967fcb7f0113` | `UNKNOWN_INTERFACE: unsupported native test configuration: unsupported addopts collection/authority option: --doctest-modules` |
| case-002 | `keleshev/schema@340d3f0596b985db9e7c81a1233f784648d7c101` | `UNKNOWN_DYNAMIC_METADATA` |
| case-003 | `mahmoud/boltons@967864f89791509f9eb36b22b4579d36b72a6df2` | `UNKNOWN_NO_COMPATIBLE_PROFILE` |
| case-004 | `mverleg/pyjson_tricks@45b96aeebc9b389f556e4af9e456d16b1d871f9d` | `UNKNOWN_DYNAMIC_METADATA` |
| case-005 | `python-humanize/humanize@4c85c352664f6ed33b00b98e52c2232081ca943d` | `UNKNOWN_METADATA_GRAMMAR` |
| case-006 | `tkem/cachetools@f4f288579dc3c8f82f62d0eaca7774303d9d3768` | `UNKNOWN_METADATA_GRAMMAR` |

The JSON companion records exact author-head metadata commits, tree/manifest/source hashes, raw record/archive hashes, and every configuration or fixture file supporting the findings below. Author-head production was not fetched; only case001 retained author-test content.

## case-000 — davidhalter/parso

The selector parses every tracked .py file before setup metadata; E10.py is intentional malformed parser input, excluded by pytest configuration and consumed as bytes.

Declared author-test head: `88874a5a9fb6114cb1a8236a4f30fa2e103f91e5`. Base tree: `398e1921df2ed4406c78bbeb9591797fd094fc9d`; source byte map SHA-256: `6606bb358b2c4c8d1e9b05abf2354d8fc8c8b674f7b8f0688da106c73b11cc0c`.

Minimum justified general behavior:

- Inventory every tracked byte and hash, including invalid syntax used as data; inventory success must not require compiling all .py files.
- Derive environment constraints from actual metadata and declared interpreter/test configuration; intentional nonimported fixture syntax must not veto unrelated environment inference.
- Preserve configured exclusions, doctests, conftest parametrization, and tests consuming malformed input.
- Let native collection and execution compile/import modules exactly as the suite normally does. Preserve suite-declared skips and expected/caught errors; do not suppress uncaught syntax/import collection failures.

Remaining boundaries:

- `UNKNOWN_DEPENDENCY_UNSATISFIED`: The frozen catalog has no docopt pin, required by the testing extra; removing the parser veto alone cannot admit either frozen profile.
- `UNKNOWN_RUNTIME_COMPATIBILITY`: Python3.6 has direct tox/CI evidence. Broad python_requires alone does not establish Python3.12: this source ships grammar files only through3.10 and defaults grammar to the running Python.
- `UNKNOWN_NATIVE_AUTHORITY`: Doctest/import collection, original-plus-author tests, and native behavior have not run.

Hashed supporting sources: `setup.py`, `pytest.ini`, `tox.ini`, `.travis.yml`, `conftest.py`, `test/test_normalizer_issues_files.py`, `test/normalizer_issue_files/E10.py`, `parso/grammar.py`, `parso/__init__.py`.

## case-001 — grantjenks/python-sortedcontainers

Source environment selection succeeded for CPython3.6.5/pytest5.4.3, but static suite authority refused --doctest-modules before collection.

Declared author-test head: `80a1ce9f8b353918974a0ca7ffdfb32c43821026`. Base tree: `fe92b5886f47c90270ce565a77b68e1809e4bd3c`; source byte map SHA-256: `a5fff3038cf8061a6e2cb8901c375ab2c1e7c7c9104cb8e8ff4df86a25bef1b7`.

Minimum justified general behavior:

- Represent declared doctest module/file collection, globs, configured roots, and ignores in immutable suite authority.
- Retain pytest-native doctest item identities and expected outcomes alongside ordinary Python tests; do not drop doctests or rewrite addopts.
- Bind original and author-test sources separately and preserve production bytes; compare authentic native collections/executions before eligibility.
- Unsupported collection/authority options remain precise UNKNOWN_INTERFACE instead of silently being waived.

Remaining boundaries:

- `UNKNOWN_NATIVE_AUTHORITY`: No native collection or execution receipt exists. Static recognition of doctest switches cannot establish their item inventory, execution outcomes, or admission.
- `UNKNOWN_EXECUTABLE_SOURCE`: Doctest module collection imports executable modules; syntax/import errors must fail normally.

Hashed supporting sources: `setup.py`, `tox.ini`, `.travis.yml`.

## case-002 — keleshev/schema

setup.py uses install_requires=open("requirements.txt", "r").read().split("\n"), which is outside V3 literal AST metadata grammar.

Declared author-test head: `d81871b8644e3b5dcc36b63904f7e3463c92a947`. Base tree: `fedb9efbcfedb243c8ca5ce0df95d4dd53ea98af`; source byte map SHA-256: `4b8b00f667dd44db88b8f7add79180011435a23e850cc7941804622ae442d060`.

Minimum justified general behavior:

- Support a finite source-local read-only requirements-file expression only if its exact syntax, literal canonical path, encoding/read/split semantics, and referenced bytes are understood and hashed.
- Preserve requirement markers and provenance; evaluate the python_version<3.3 marker against each candidate runtime.
- Continue refusing arbitrary setup execution, aliases, reflection, unknown calls, mutable metadata, traversal, and unbound file inputs.
- Preserve selected test-lane dependencies, mypy subprocess/skip behavior, and any supported documentation obligations.

Remaining boundaries:

- `UNKNOWN_DYNAMIC_METADATA`: The exact read/split expression needs bounded generic support; no setup.py was executed for this analysis.
- `UNKNOWN_DEPENDENCY_UNSATISFIED`: Frozen profiles do not pin mock or mypy from the tox test environment. The original grammar failure occurred before this dependency question.
- `UNKNOWN_NATIVE_AUTHORITY`: Source-file extraction alone cannot establish native test or subprocess coverage, nor authorize suppressing skipped tests.

Hashed supporting sources: `setup.py`, `requirements.txt`, `tox.ini`, `pyproject.toml`, `.github/workflows/python-test.yml`, `.travis.yml`, `test_mypy_use_callable.py`.

## case-003 — mahmoud/boltons

Metadata was derived successfully. Python3.6 is incompatible, and Python3.12 has flit_core4.0.1 while the project requires >=3.2,<4.

Declared author-test head: `f268ec349d4a4f13e3e8f2dd86db059959514222`. Base tree: `5f96239ad4d6613b175f4d57732963a99ecb125a`; source byte map SHA-256: `9dfdb5cc6e533f38fede59ec5b94844ed2342fdd71ef1e649eb9ba0baabbaa92`.

Minimum justified general behavior:

- Retain the exact flit_core<4 constraint and reject or report UNKNOWN for the frozen incompatible inventory; do not weaken a source requirement to create compatibility.
- A future catalog may add a separately pinned/provenance-bound compatible backend before task admission, with dependency closure verified.
- Resolve the selected tox dependency group and marker-aware pytest requirement; preserve changedir, installed-package doctests, original tests, and effective command semantics.

Remaining boundaries:

- `UNKNOWN_NO_COMPATIBLE_PROFILE`: The original frozen catalog has no compatible profile; no provisioning or inventory amendment occurred.
- `UNKNOWN_NATIVE_AUTHORITY`: Doctests, installed-package import paths, tox-uv/dependency group behavior, and native execution remain unqualified.

Hashed supporting sources: `pyproject.toml`, `tox.ini`, `.github/workflows/tests.yaml`.

## case-004 — mverleg/pyjson_tricks

setup.py binds requires=[], conditionally appends ordereddict for Python<2.7, then passes install_requires=requires. V3 rejects the referenced list method call.

Declared author-test head: `47caad0baf1f555f8e2cc35739f1d3e1796233c9`. Base tree: `9ba5b1f7df35427663cf5914aace67f67f4cf22a`; source byte map SHA-256: `39f0e33ba700c3b22c38d3244d7c20c1d5b17d7beb227a69b138dbd45e28c50b`.

Minimum justified general behavior:

- Either interpret a precisely bounded version_info comparison plus literal list-append grammar per candidate profile, or retain UNKNOWN_DYNAMIC_METADATA with exact branch/mutation provenance.
- Track binding identity, statement order, aliasing, branches, and mutations; do not ignore all method calls or union away interpreter-conditional dependency semantics.
- For the two frozen Python3 profiles, a correctly interpreted version_info<(2,7,0) guard would be false; this fact alone supplies no complete native-suite warrant.
- Native authority must bind an intended source-declared dependency/test lane and preserve all its tests; it cannot silently pick a smaller lane to avoid numpy/pandas or other imports.

Remaining boundaries:

- `UNKNOWN_DYNAMIC_METADATA`: No generic interpreter-conditional mutation support is implemented or exercised here.
- `UNKNOWN_NATIVE_TEST_LANE`: CI has several legitimate dependency/test matrices. A full original-suite claim needs the declared dependencies/import behavior and cannot be inferred from vanilla setup dependencies.
- `UNKNOWN_NATIVE_AUTHORITY`: No collection or execution evidence exists.

Hashed supporting sources: `setup.py`, `setup.cfg`, `.github/workflows/tests.yml`, `tests/run_locally.md`.

## case-005 — python-humanize/humanize

tox.ini declares py{310-315} and py{314-315}t. V3 bounds numeric factor endpoints to99, so these finite Python minor-version encodings are reported as unbounded expansion.

Declared author-test head: `eda405bd598b7d5e17eca1c11b76cfbe011aa5da`. Base tree: `f457adceb2cc27becb090b4a6607ec8b6df54f10`; source byte map SHA-256: `9eaf9e01efc163e6bf28d41eace1281ec56b13fe12aeb92412edd7634dcb60c9`.

Minimum justified general behavior:

- Bound expansion by finite cardinality and supported factor syntax, with resource limits; finite310–315 endpoints are not intrinsically unbounded.
- Interpret CPython version factors, PyPy factors, generic py selection, and free-threaded t variants without collapsing distinct interpreter/ABI requirements.
- Preserve tests extras, modern pytest configuration precedence/version semantics, effective doctest and coverage behavior, plugin identities, generated translations, and build inputs.

Remaining boundaries:

- `UNKNOWN_METADATA_GRAMMAR`: Bounded version-factor/free-threaded interpretation has not been implemented or qualified.
- `UNKNOWN_NO_COMPATIBLE_PROFILE`: After recognizing grammar, neither frozen profile satisfies pytest>=9 (pins5.4.3/8.4.1). Frozen inventories also lack freezegun, pytest-codspeed, and pytest-cov.
- `UNKNOWN_GENERATED_BUILD_INPUT`: gettext/msgfmt translation artifacts and their source/generated provenance remain unqualified.
- `UNKNOWN_NATIVE_AUTHORITY`: No native collection/execution occurred; honoring one legacy or modern config table while discarding another is not justified.

Hashed supporting sources: `tox.ini`, `pyproject.toml`, `.github/workflows/test.yml`, `scripts/generate-translation-binaries.sh`.

## case-006 — tkem/cachetools

tox.ini has envlist=py,docs,doctest,pyright,ruff,ruff-format; bare py is an unversioned selected-interpreter test environment, which V3 rejects.

Declared author-test head: `2417c0d63b286772169c0eab4ccf141213e1ca45`. Base tree: `5cdf6f106387e0fcf3e7585213ef1d5ac61ad9ac`; source byte map SHA-256: `179316b66b6f6b45a09cd13e5d34de2e2b16a1bd209324ee4a673e421f0ddf37`.

Minimum justified general behavior:

- Recognize bare tox py as imposing no independent version restriction; combine it with actual project/CI interpreter evidence rather than fabricating a version.
- Separate explicitly identified auxiliary environment names from interpreter factors; ambiguous interpreter declarations remain precise UNKNOWN.
- Reject Python3.6 under requires-python>=3.10; Python3.12 has positive project/CI compatibility evidence subject to actual pinned dependency closure.
- Install the src-layout project through the declared build system and retain pytest-cov/effective command flags.
- Use native collection for inherited unittest/mixin item identities instead of top-level static function counts.

Remaining boundaries:

- `UNKNOWN_DEPENDENCY_UNSATISFIED`: The frozen modern profile has setuptools/setuptools-scm but no pytest-cov pin. Its compatible interpreter alone is insufficient.
- `UNKNOWN_NATIVE_AUTHORITY`: Build/install, source roots, inherited collection identities, coverage plugin, and native execution have not been verified.

Hashed supporting sources: `tox.ini`, `pyproject.toml`, `.github/workflows/ci.yml`, `tests/__init__.py`.

## Preservation and verification

Independently reconciled all 1,351 regular-file entries in the original retained post-audit inventory. Checked 687 tracked source files against immutable Git blob identities, manifest and selector source hashes, plus 9 source archives against expected bytes without extraction. All checks passed.

Before any Git read, independently copied all 63 observed workspace indexes to `/tmp/v4-diagnostic-index-snapshots`. Git reads used `GIT_OPTIONAL_LOCKS=0`; all eight generated V3 indexes are byte-identical before/after this recovery. The JSON records the before/after hashes and snapshot paths. These copies establish preservation during this recovery, not the missing historical pre-audit index state.

No task Python was imported or executed. The frozen selector/auditor were not rerun. Environment candidate selection, inventory integrity and native success remain separate claims. All seven cases must remain excluded from future prospective held-out evaluation.
