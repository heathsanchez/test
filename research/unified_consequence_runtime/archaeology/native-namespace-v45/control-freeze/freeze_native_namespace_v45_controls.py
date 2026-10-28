"""Hand-derived local qualification inputs; never imports or executes UDM code."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path('/workspace/qualification/native-namespace-v45-control-freeze')
SOURCE = Path('/workspace/udm-v54')
BASE = '88aa5090c310d2f75683a019a5bc958cdb3b576e'
assert not ROOT.exists(), 'new outside directory required'
ROOT.mkdir(parents=True)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode() + b'\n'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def write(name, raw):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw if isinstance(raw, bytes) else raw.encode())

BASE_TEST = 'from library.constants import *\ndef test_contract():\n    assert ANSWER == 41\n'
AUG_TEST = BASE_TEST.replace('ANSWER == 41', 'ANSWER == 42')
CONSTANTS = ('ANSWER = 42\nVALUES = (41, 42)\nclass Node:\n    pass\n'
             'def describe():\n    return ANSWER\n_hidden = 99\n')
COMMON = {'pytest.ini': '[pytest]\naddopts = --import-mode=importlib\n',
          'library/__init__.py': '', 'library/constants.py': CONSTANTS}
cases = []

def case(name, category, expected, reason, *, before=BASE_TEST, after=AUG_TEST,
         files=None, scope='CORE', nodes=None, exports=None):
    mapping = dict(COMMON)
    mapping.update(files or {})
    variants = {}
    for variant, test in [('baseline', before), ('augmented', after)]:
        complete = dict(mapping, **{'tests/test_native.py': test})
        variants[variant] = {}
        for path, text in sorted(complete.items()):
            raw = text if isinstance(text, bytes) else text.encode()
            write('fixtures/' + name + '/' + variant + '/' + path, raw)
            variants[variant][path] = {'sha256': digest(raw), 'bytes': len(raw), 'mode': '100644'}
    row = dict(id=name, category=category, expected=expected, reason=reason, scope=scope,
               source_variants=variants, expected_changed_paths=['tests/test_native.py'])
    if nodes is not None:
        row['hand_derived_required_node_prefixes'] = nodes
    if exports is not None:
        row['hand_derived_wildcard_exports'] = exports
    cases.append(row)

case('W01_closed_production_wildcard', 'wildcard', 'ADMIT_THEN_PASS_NATIVE',
     'One exact local declaration; production names contain no test/collector authority. No __all__, __getattr__, import or class initializer effects.',
     nodes=['tests/test_native.py::test_contract'],
     exports=['ANSWER', 'Node', 'VALUES', 'describe'])
case('W02_unimported_malformed_python_data', 'malformed-data', 'ADMIT_THEN_PASS_NATIVE',
     'A tracked .py payload is data because it is never imported; do not compile every tracked Python-looking byte.',
     files={'fixtures/python2_payload.py': b'print "payload data"\n'},
     nodes=['tests/test_native.py::test_contract'])
case('W03_collection_imported_malformed_python', 'malformed-import', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'The wildcard target is authoritative import source and cannot be parsed under the selected Python; never treat it as inert data.',
     files={'library/constants.py': 'ANSWER = 42\nprint "payload data"\n'})
case('W04_runtime_imported_malformed_python', 'malformed-import', 'ADMIT_THEN_FAIL_NATIVE',
     'A runtime import inside the actual original test raises SyntaxError; preserve ordinary native failure rather than masking it as data.',
     after='from library.constants import *\ndef test_contract():\n    import fixtures.python2_payload\n    assert ANSWER == 42\n',
     files={'fixtures/__init__.py': '', 'fixtures/python2_payload.py': b'print "payload data"\n'},
     nodes=['tests/test_native.py::test_contract'])
case('W05_wildcard_public_function_test', 'wildcard-test', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'Imported callable matches configured test grammar; cannot count imported assertions as source-local declarations.',
     files={'library/constants.py': CONSTANTS + 'def test_foreign():\n    assert True\n'})
case('W06_wildcard_public_test_class', 'wildcard-test', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'A Test-prefixed export can introduce native collection even with no local function declaration.',
     files={'library/constants.py': CONSTANTS + 'class TestForeign:\n    def test_injected(self):\n        assert True\n'})
case('W07_literal_all_test_hiding', 'export-protocol', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'Even literal __all__ is outside the minimum no-export-protocol grammar; spelling alone is no certificate.',
     files={'library/constants.py': CONSTANTS + '__all__ = ["ANSWER"]\ndef test_hidden():\n    assert True\n'})
case('W08_all_getattr_fabricated_export', 'export-protocol', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     '__getattr__ can fabricate an export named in __all__; do not trust a hand-written export list.',
     files={'library/constants.py': 'ANSWER = 42\n__all__ = ["ANSWER", "test_fabricated"]\ndef __getattr__(name):\n    return lambda: None\n'})
case('W09_getattr_without_all', 'export-protocol', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'Dynamic export protocol remains unsupported by the narrow static source-local contract.',
     files={'library/constants.py': CONSTANTS + 'def __getattr__(name):\n    return ANSWER\n'})
case('W10_reexport_origin', 'origin', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'Minimum contract has one directly defined source-local namespace. Reexports need additional complete recursive origin evidence.',
     files={'library/constants.py': 'from library.leaf import ANSWER\n', 'library/leaf.py': 'ANSWER = 42\n'})
case('W11_test_alias_export', 'alias', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'Alias to a callable has test grammar even when its origin helper did not.',
     files={'library/constants.py': CONSTANTS + 'test_alias = describe\n'})
case('W12_class_alias_export', 'alias', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'A Test-prefixed alias to a class can create a collection route.',
     files={'library/constants.py': CONSTANTS + 'TestAlias = Node\n'})
case('W13_wildcard_after_local_shadowing', 'shadowing', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'A source-local changed assertion is rebound after definition by the wildcard import.',
     before='def test_contract():\n    assert False\nfrom library.constants import *\n',
     after='def test_contract():\n    assert 1 == 2\nfrom library.constants import *\n',
     files={'library/constants.py': 'ANSWER = 42\ndef test_contract():\n    pass\n'})
case('W14_package_initializer_effect', 'origin', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'All package initializers on the imported route belong to the origin closure; validating only constants.py is insufficient.',
     files={'library/__init__.py': 'import builtins\nbuiltins.NAMESPACE_FREEZE_MUTATED = True\n'})
case('W15_export_opaque_call', 'origin', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'Source-local does not imply inert: opaque collection-time calls can change test state.',
     files={'library/constants.py': 'def compute():\n    return 42\nANSWER = compute()\n'})

PLAIN_BEFORE = 'def test_contract():\n    assert False\n'
PLAIN_AFTER = 'def test_contract():\n    assert 1 == 2\n'
case('B01_same_prefix_literal_rebound', 'binding', 'REFUSE_OR_UNKNOWN_NO_ADMISSION',
     'The static declaration remains in the AST but its name now binds data; prefix existence alone cannot authorize it.',
     before=PLAIN_BEFORE + 'test_contract = 7\n', after=PLAIN_AFTER + 'test_contract = 7\n')
DECORATOR = ('def erase(original):\n    def wrapper():\n        pass\n    return wrapper\n'
             '@erase\n')
case('B02_same_prefix_noop_decorator', 'binding', 'REFUSE_OR_UNKNOWN_NO_ADMISSION',
     'Collection and independent recollection can consistently see the same no-op wrapper. Bind the original declaration to the actual outer callable.',
     before=DECORATOR + PLAIN_BEFORE, after=DECORATOR + PLAIN_AFTER)
WRAPPED = ('def erase(original):\n    def wrapper():\n        pass\n'
           '    wrapper.__wrapped__ = original\n    return wrapper\n@erase\n')
case('B03_forged_wrapped_noop', 'binding', 'REFUSE_OR_UNKNOWN_NO_ADMISSION',
     'Original code_hash follows __wrapped__, but Python invokes the outer no-op. A hash of an unwrapped object does not prove assertion execution.',
     before=WRAPPED + PLAIN_BEFORE, after=WRAPPED + PLAIN_AFTER)
case('B04_deleted_local_test', 'binding', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'Deleted original assertion cannot be licensed by successful collection of another test.',
     before=PLAIN_BEFORE + 'del test_contract\n', after=PLAIN_AFTER + 'del test_contract\n')
case('B05_imported_same_prefix_alias', 'binding', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'Explicit imported alias replaces the original assertion with a foreign no-op.',
     before=PLAIN_BEFORE + 'from library.other import noop as test_contract\n',
     after=PLAIN_AFTER + 'from library.other import noop as test_contract\n',
     files={'library/other.py': 'def noop():\n    pass\n'})
case('B06_duplicate_local_definition', 'binding', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'Two same-name definitions cannot both be represented by one exact collected object.',
     before=PLAIN_BEFORE + 'def test_contract():\n    pass\n',
     after=PLAIN_AFTER + 'def test_contract():\n    pass\n')
case('B07_missing_collection_test_false', 'missing', 'REFUSE_OR_UNKNOWN_NO_ADMISSION',
     'A changed class method with __test__ = False has no native collection witness.',
     before='class TestLocal:\n    __test__ = False\n    def test_contract(self):\n        assert False\n',
     after='class TestLocal:\n    __test__ = False\n    def test_contract(self):\n        assert 1 == 2\n')
case('B08_class_method_rebound', 'binding', 'REFUSE_OR_UNKNOWN_NO_ADMISSION',
     'Class inheritance mapping must retain declaration identity when a method name is overwritten by data.',
     before='class TestLocal:\n    def test_contract(self):\n        assert False\n    test_contract = 7\n',
     after='class TestLocal:\n    def test_contract(self):\n        assert 1 == 2\n    test_contract = 7\n')

ORDER_PREFIX = ('import unittest\ndef reverse_names(left, right):\n'
                '    return (left < right) - (left > right)\n'
                'unittest.TestLoader.sortTestMethodsUsing = staticmethod(reverse_names)\n')
ORDER_BODY = ('class NativeCase(unittest.TestCase):\n    def test_a(self):\n'
              '        assert 42 == 41\n    def test_b(self):\n        assert True\n')
case('O01_deterministic_order_only_hook', 'order', 'ADMIT_THEN_PASS_NATIVE_IF_ORDER_SUBSET_SUPPORTED',
     'Optional narrow ordering subset: original unittest target, inert source-local comparator, exact changed assertion bindings, exact independent order test_b then test_a.',
     before=ORDER_PREFIX + ORDER_BODY,
     after=ORDER_PREFIX + ORDER_BODY.replace('42 == 41', '42 == 42'),
     scope='OPTIONAL_ORDER_SUBSET',
     nodes=['tests/test_native.py::NativeCase::test_a', 'tests/test_native.py::NativeCase::test_b'])
RANDOM_PREFIX = ('import unittest\nimport os\nSALT = os.urandom(10)\n'
                 'def random_names(left, right):\n'
                 '    return (hash(SALT + left.encode()) > hash(SALT + right.encode())) - (hash(SALT + left.encode()) < hash(SALT + right.encode()))\n'
                 'unittest.TestLoader.sortTestMethodsUsing = staticmethod(random_names)\n')
case('O02_entropy_salted_order_hook', 'order', 'REFUSE_UNKNOWN_ORDER_AUTHORITY',
     'No deterministic source-local order proof; preserve this obstruction. Never sort, seed, retry, shim entropy or weaken exact replay.',
     before=RANDOM_PREFIX + ORDER_BODY,
     after=RANDOM_PREFIX + ORDER_BODY.replace('42 == 41', '42 == 42'))
case('O03_test_method_prefix_write', 'namespace-write', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'Attribute target changes collection authority, not only order.',
     before='import unittest\nunittest.TestLoader.testMethodPrefix = "noop"\n' + ORDER_BODY,
     after='import unittest\nunittest.TestLoader.testMethodPrefix = "noop"\n' + ORDER_BODY.replace('42 == 41', '42 == 42'))
case('O04_globals_subscript_write', 'namespace-write', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'General namespace writes remain outside authority.',
     before=PLAIN_BEFORE + 'globals()["test_contract"] = lambda: None\n',
     after=PLAIN_AFTER + 'globals()["test_contract"] = lambda: None\n')
FAKE = ('class Dummy:\n    pass\nunittest = Dummy()\nunittest.TestLoader = Dummy()\n'
        'def reverse_names(left, right):\n    return 0\n'
        'unittest.TestLoader.sortTestMethodsUsing = staticmethod(reverse_names)\n')
case('O05_shadowed_order_target', 'shadowing', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'Do not recognize an ordering capability by attribute spelling after unittest was shadowed.',
     before=FAKE + PLAIN_BEFORE, after=FAKE + PLAIN_AFTER)
EFFECT = ('import unittest\ndef reverse_names(left, right):\n'
          '    globals()["test_contract"] = lambda: None\n    return 0\n'
          'unittest.TestLoader.sortTestMethodsUsing = staticmethod(reverse_names)\n')
case('O06_effectful_comparator', 'order', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'An ordering comparator that writes namespace also changes assertion authority.',
     before=EFFECT + PLAIN_BEFORE, after=EFFECT + PLAIN_AFTER)
case('O07_other_attribute_write', 'namespace-write', 'REFUSE_UNKNOWN_BEFORE_NATIVE',
     'The extension must not blanket-allow attribute or subscript writes.',
     before='import unittest\nunittest.TestCase.__test__ = False\n' + ORDER_BODY,
     after='import unittest\nunittest.TestCase.__test__ = False\n' + ORDER_BODY.replace('42 == 41', '42 == 42'))

tamper_rows = [
    ('R01_stale_source', 'Use W01 authority/certificate with different augmented test source or commit.', 'Original exact reconstructed authority/source identity'),
    ('R02_forged_required_set', 'Delete test_contract from required assertion set, reseal public hashes.', 'Original exact reconstructed authority'),
    ('R03_forged_export_set', 'Omit a W05/W06 test-like export from claimed namespace, reseal public hashes.', 'NEW independent closed namespace derivation'),
    ('R04_wrong_export_origin', 'Change constants.py origin hash/path to leaf.py while preserving ANSWER and test counts.', 'NEW origin closure plus inherited import/source checks'),
    ('R05_wrong_declaration_binding', 'Claim W01 declaration for B02/B03 outer wrapper and reseal all packet hashes.', 'NEW independently compiled actual executable binding'),
    ('R06_missing_protected_node', 'Remove required collected node and its item entry; retain unrelated passing node.', 'Original protected-prefix and independent replay'),
    ('R07_partial_parameter_deselection', 'Remove one [second] parameter case from collected/selected/items and reseal packet.', 'Original full exact independent collection and no deselection'),
    ('R08_missing_call_report', 'Retain collection item but delete its setup/call/teardown or call evidence.', 'Original strict report sequences and counts'),
    ('R09_skipped_or_xfailed_assertion', 'Mark a required report skipped/xfail/strict-xpass with matching JUnit counts.', 'Original no-skip/no-xfail required execution'),
    ('R10_resealed_receipt', 'Change report/item/source/import bytes and recompute every public digest.', 'Original independent recollection/reexecution; NEW declaration binding'),
    ('R11_environment_replacement', 'Replay same certificate under changed interpreter/stdlib/pytest bytes or identity.', 'Original pinned environment and host identity'),
    ('R12_plugin_replacement', 'Replace licensed plugin file/distribution or register unlicensed plugin with same module name.', 'Original licensed distribution, content, manifest and replay'),
    ('R13_independent_order_mismatch', 'Present one order, then independently recollect reversed selected order with same set/counts.', 'Original ordered equality, never set-only or sorted equality'),
    ('R14_execution_order_mismatch', 'Preserve certificate collection but reverse call/setup/teardown order at execution.', 'Original exact report order'),
    ('R15_changed_imported_source', 'Candidate changes wildcard target public exports or initializer effects while tests stay byte-identical.', 'NEW namespace revalidation per executable view; no stale source namespace authority'),
    ('R16_missing_namespace_binding', 'Remove namespace/declaration binding evidence or substitute unknown schema/revision.', 'NEW exact versioned schema and fail-closed bridge'),
    ('R17_candidate_test_or_config_edit', 'Candidate replaces test_native.py, conftest.py, pytest.ini or supplies own namespace/authority.', 'Original production-only candidate grammar and external authority'),
    ('R18_observed_code_changes_after_collection', 'Mutate outer callable.__code__ between collection and call.', 'Original code-change check plus NEW outer callable check'),
]
replay = [dict(id=i, category='replay/tamper', source_case='W01_closed_production_wildcard',
               operation=op, expected='REFUSE_OR_UNKNOWN_NEVER_PASS', support=support)
          for i, op, support in tamper_rows]

syntax = []
for row in cases:
    for variant, manifest in row['source_variants'].items():
        for path in manifest:
            if not path.endswith('.py'):
                continue
            raw = (ROOT/'fixtures'/row['id']/variant/path).read_bytes()
            try:
                ast.parse(raw, filename=path)
                result = 'PARSEABLE'
            except SyntaxError:
                result = 'INTENTIONALLY_MALFORMED'
                assert path in ('fixtures/python2_payload.py', 'library/constants.py') and row['id'] in (
                    'W02_unimported_malformed_python_data', 'W03_collection_imported_malformed_python',
                    'W04_runtime_imported_malformed_python')
            syntax.append(dict(case=row['id'], variant=variant, path=path, result=result))

source_paths = [
    'native_admission_v2.py', 'native_admission_v42.py', 'native_execution_v2.py',
    'native_execution_v3.py', 'native_execution_v42.py', 'native_execution_v43.py',
    'test_native_admission_v2_adversarial.py', 'test_native_authority_v4.py',
    'test_native_execution_v3.py', 'test_native_suite_authority.py',
]
pins = {}
for name in source_paths:
    relative = 'research/unified_consequence_runtime/' + name
    pins[relative] = digest((SOURCE/relative).read_bytes())

write('FIXTURE_INDEX.json', canonical(dict(schema='HAND_DERIVED_NAMESPACE_V45_CONTROL_FREEZE_1',
    baseline_repository='heathsanchez/test', baseline_commit=BASE,
    independence='Fixtures and expected outcomes hand-derived before production extension; no UDM modules imported or tasks executed.',
    cases=cases, replay_controls=replay)))
write('SOURCE_PINS.json', canonical(dict(baseline_commit=BASE, sha256=pins)))
write('SYNTAX_ONLY_CHECK.json', canonical(dict(method='Python stdlib ast.parse on frozen synthetic inputs only; no import, collection or native calls.', rows=syntax)))
write('freeze_native_namespace_v45_controls.py', Path(__file__).read_bytes())
print(json.dumps(dict(directory=str(ROOT), source_cases=len(cases), replay_controls=len(replay), syntax_rows=len(syntax)), sort_keys=True))
