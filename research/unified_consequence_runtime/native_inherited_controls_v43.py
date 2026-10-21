"""Executable postimplementation V43 binding of original adversarial methods.

No original test statement or source file changes.  Only the fixture's source,
suite-authority and worker dependencies and explicit V43 schemas are rebound.
This qualifies the V43 binding; it does not relabel a V42 result as a V43 run.
"""
from __future__ import annotations

import argparse
import inspect
from pathlib import Path
import shutil
import sys
from types import FunctionType
import unittest

from . import native_execution_v43 as execution
from . import test_native_admission_v2_adversarial as controls


def inherited_suite(retained_cases=None):
    realm = dict(vars(controls), execution=execution, admission=execution.admission,
                 frozen=execution.original)
    methods, identity = {}, {}
    for name, value in vars(controls.NativeAdmissionV2AdversarialTests).items():
        if isinstance(value, FunctionType):
            rebound = FunctionType(value.__code__, realm, value.__name__, value.__defaults__, value.__closure__)
            rebound.__kwdefaults__ = value.__kwdefaults__
            assert rebound.__code__ is value.__code__
            methods[name] = rebound
            identity[name] = execution.sha256(inspect.getsource(value).encode())
    refresh = methods['refresh']
    original_setup = methods['setUp']
    def versioned_refresh(self):
        refresh(self)
        self.contract.update(schema=execution.SCHEMA, generated_build=None)
    def setup(cls):
        cls.environment = execution.environment_identity(sys.executable)
        cls.policy = {'schema': execution.POLICY_SCHEMA, 'collection_seconds': 15, 'execution_seconds': 15,
            'pytest_version': cls.environment['pytest_version'], 'plugins': []}
    methods.update(refresh=versioned_refresh, setUpClass=classmethod(setup))
    if retained_cases is not None:
        retained_cases = Path(retained_cases)
        def retained_setup(self):
            try:
                original_setup(self)
            finally:
                if hasattr(self, 'root'):
                    destination = retained_cases/self.id()
                    def retain():
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(self.root, destination, symlinks=True)
                    # Original setUp registered TemporaryDirectory cleanup first.
                    # LIFO cleanup preserves its exact native evidence before it.
                    self.addCleanup(retain)
        methods['setUp'] = retained_setup
    return type('NativeV43InheritedAdversarialTests', (unittest.TestCase,), methods), identity


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output).absolute()
    if output.exists() or output.resolve() != output:
        raise ValueError('new canonical inherited-control evidence directory required')
    output.mkdir(parents=True)
    case, identity = inherited_suite(output/'cases')
    provenance = {'schema': 'UDM_INHERITED_NATIVE_CONTROLS_V43',
        'classification': 'POSTIMPLEMENTATION_PRIVATE_DEPENDENCY_BINDING',
        'runner_sha256': execution.sha256(Path(__file__).read_bytes()),
        'worker_sha256': execution._runner_hash(),
        'original_test_source_sha256': execution.sha256(Path(controls.__file__).read_bytes()),
        'original_method_source_sha256': identity,
        'test_method_code_objects_unchanged': True,
        'fixture_adapters': ['dependency globals', 'refresh schema and explicit generated_build=None',
                             'setUpClass versioned policy and actual interpreter environment',
                             'post-original-setUp cleanup copies complete case evidence before original temporary cleanup']}
    (output/'provenance.json').write_text(execution.canonical(provenance)+'\n')
    (output/'runner-source.py').write_bytes(Path(__file__).read_bytes())
    (output/'original-test-source.py').write_bytes(Path(controls.__file__).read_bytes())
    with (output/'unittest.log').open('w') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(case))
    report = dict(provenance, tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        status='PASS' if result.wasSuccessful() else 'FAIL',
        attempts=execution.attempt_snapshot(), builds=execution.build_snapshot())
    (output/'result.json').write_text(execution.canonical(report)+'\n')
    print(execution.canonical({key: report[key] for key in ('status', 'tests', 'failures', 'errors')}))
    return int(not result.wasSuccessful())


if __name__ == '__main__':
    raise SystemExit(main())
