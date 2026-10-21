"""Run original adversarial test code objects with explicit V43 dependencies."""
from pathlib import Path
from types import FunctionType
import sys
import unittest

sys.path.insert(0, '/workspace/udm-v54')
from research.unified_consequence_runtime import native_execution_v43 as execution
from research.unified_consequence_runtime import test_native_admission_v2_adversarial as controls

realm = dict(vars(controls), execution=execution, admission=execution.admission, frozen=execution.original)
methods = {}
for name, value in vars(controls.NativeAdmissionV2AdversarialTests).items():
    if isinstance(value, FunctionType):
        methods[name] = FunctionType(value.__code__, realm, value.__name__, value.__defaults__, value.__closure__)
refresh = methods['refresh']


def versioned_refresh(self):
    refresh(self)
    self.contract.update(schema=execution.SCHEMA, generated_build=None)


def setup(cls):
    cls.environment = execution.environment_identity(sys.executable)
    cls.policy = {'schema': execution.POLICY_SCHEMA, 'collection_seconds': 15, 'execution_seconds': 15,
        'pytest_version': cls.environment['pytest_version'], 'plugins': []}


methods['refresh'] = versioned_refresh
methods['setUpClass'] = classmethod(setup)
case = type('NativeV43InheritedAdversarialTests', (unittest.TestCase,), methods)
folder = Path('/workspace/qualification/experiment-interface-v43-native-implementation')
with (folder/'inherited-adversarial-retry.log').open('w') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(case))
print({'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'log': str(folder/'inherited-adversarial-retry.log')})
raise SystemExit(not result.wasSuccessful())
