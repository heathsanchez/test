"""Local V43 transport controls; no prospective tasks or original source edits."""
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, '/workspace/udm-v54')
from research.unified_consequence_runtime import native_execution_v43 as worker
from research.unified_consequence_runtime import native_build_v43 as build
from research.unified_consequence_runtime.native_v43_test_support import make_project, MODERN_PYTHON

root = Path('/workspace/qualification/experiment-interface-v43-native-implementation/supplementary-fixtures')
root.mkdir()
environment = worker.environment_identity(str(MODERN_PYTHON))
results = []


def rejected(label, operation):
    try:
        operation()
    except ValueError as error:
        results.append({'control': label, 'result': 'REJECTED', 'reason': str(error)})
    else:
        raise AssertionError('control unexpectedly admitted: ' + label)


def warm(case, folder):
    evidence = build.prepare(case.contract, case.authority, case.policy, folder/'prepare')
    return case.with_evidence(evidence)


case = make_project(root/'honest', 'alpha', environment)
contract = warm(case, root/'honest')
certificate = worker.collect(contract, case.authority, root/'honest/collection', policy=case.policy)
receipt = worker.verify(contract, {'replacements': []}, root/'honest/native',
    authority=case.authority, admission_certificate=certificate, policy=case.policy)
assert receipt['status'] == 'PASS_NATIVE'
assert worker.validate_receipt(contract, {'replacements': []}, case.authority, certificate,
    receipt, policy=case.policy, independent=False)['status'] == 'PASS_NATIVE'
results.append({'control': 'honest-accounted-native', 'result': receipt['status']})


def validate(value):
    return worker.validate_receipt(contract, {'replacements': []}, case.authority,
        certificate, value, policy=case.policy, independent=False)


missing = copy.deepcopy(receipt)
missing['independent_collection'].pop('build_verification')
rejected('missing-build-accounting', lambda: validate(missing))
sidecar = root/'honest/native/independent-collection/generated-build-verification.json'
saved = sidecar.with_suffix('.saved')
sidecar.rename(saved)
try:
    rejected('missing-build-sidecar', lambda: validate(receipt))
finally:
    saved.rename(sidecar)


def consistent_clone(label, mutation):
    clone = copy.deepcopy(receipt)
    output = root/label
    (output/'generated-build-verification').mkdir(parents=True)
    clone['independent_collection']['output'] = str(output)
    record = clone['independent_collection']['build_verification']
    record['native_output'] = str(output)
    record['builder_attempts_after']['records'][-1] = str(output/'retained-build.json')
    mutation(record)
    (output/'generated-build-verification.json').write_text(worker.canonical(record)+'\n')
    (output/'generated-build-verification/verification.json').write_text(worker.canonical(record['receipt'])+'\n')
    (output/'retained-build.json').write_text(worker.canonical(record['receipt']['build'])+'\n')
    return clone


cloned = consistent_clone('unchanged-accounting-clone', lambda value: None)
assert validate(cloned)['status'] == 'PASS_NATIVE'
results.append({'control': 'unchanged-accounting-clone', 'result': 'PASS_NATIVE'})


def zero_calls(record):
    record['receipt']['costs']['build_calls'] = 0
    record['receipt']['build']['costs']['build_calls'] = 0


for label, mutation in (
    ('consistently-forged-zero-build-calls', zero_calls),
    ('consistently-forged-recipe', lambda record: record['receipt']['build'].update(recipe_sha256='0'*64)),
    ('consistently-forged-counter', lambda record: record['builder_attempts_after'].update(build_calls=0)),
):
    forged = consistent_clone(label, mutation)
    rejected(label, lambda: validate(forged))


for label, tail in (
    ('generated-mode', '    from pathlib import Path\n    import native_alpha_v43._version as version\n    Path(version.__file__).chmod(0o600)\n'),
    ('generated-parent-alias', '    from pathlib import Path\n    import native_alpha_v43._version as version\n    parent = Path(version.__file__).parent\n    saved = parent.with_name(parent.name + "_saved")\n    parent.rename(saved)\n    parent.symlink_to(saved.name, target_is_directory=True)\n'),
):
    altered = make_project(root/label, 'alpha', environment, test_tail=tail)
    augmented = warm(altered, root/label)
    admitted = worker.collect(augmented, altered.authority, root/label/'collection', policy=altered.policy)
    result = worker.verify(augmented, {'replacements': []}, root/label/'native',
        authority=altered.authority, admission_certificate=admitted, policy=altered.policy)
    assert result['status'] == 'UNKNOWN_SOURCE_OR_IMPORT_IDENTITY', result['status']
    results.append({'control': label, 'result': result['status'], 'source_mutations': result['execution']['source_mutations']})

plugin = b'def pytest_configure(config):\n    import native_alpha_v43._version as version\n    config.pluginmanager.register(version, "generated-build-plugin")\n'
plugins = make_project(root/'generated-plugin', 'alpha', environment, extra_files={'conftest.py': plugin})
augmented = warm(plugins, root/'generated-plugin')
rejected('generated-module-pytest-plugin', lambda: worker.collect(augmented, plugins.authority,
    root/'generated-plugin/collection', policy=plugins.policy))
checked = json.loads((root/'generated-plugin/collection/checked-report.json').read_bytes())
assert any(value.startswith('generated-pytest-plugin:') for value in checked['source_mutations'])
results[-1]['source_mutations'] = checked['source_mutations']

replayed = worker.validate_receipt(contract, {'replacements': []}, case.authority, certificate,
    receipt, policy=case.policy, output_dir=root/'independent-replay', independent=True)
actual = replayed['independent_build_accounting']
assert actual['verification_attempts'] == 2
assert actual['builder_attempts_after']['build_calls'] == actual['builder_attempts_before']['build_calls'] + 2
results.append({'control': 'fresh-independent-accounting', 'result': replayed['status'], 'actual': actual})
report = {'controls': results, 'attempts': worker.attempt_snapshot(), 'builds': worker.build_snapshot()}
(root.parent/'supplementary-results.json').write_text(worker.canonical(report)+'\n')
print(json.dumps({'controls': len(results), 'status': 'PASS', 'results': str(root.parent/'supplementary-results.json')}))
