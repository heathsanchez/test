"""V421 default-prepend legacy fixture; original V42/661 source remains intact.

The versioned generator declares empty addopts before its first Git
commit. Protected native test methods retain their original code objects. The
unsupported original importlib configuration remains an executed refusal.
"""
from pathlib import Path
from types import FunctionType
import unittest

from . import test_native_execution_v42 as original
from .decisive_native_verify import sha256

ORIGINAL_TEST_SHA256 = '24222b334b1bb93d54aac476a65a1f17e7904aca5c69beca72cd8505684a08b2'
ORIGINAL_CONFIGURATION = '[pytest]\naddopts=--import-mode=importlib\n'
LEGACY_CONFIGURATION = '[pytest]\naddopts=\n'


def _legacy_setup():
    if sha256(Path(original.__file__).read_bytes()) != ORIGINAL_TEST_SHA256:
        raise ValueError('UNKNOWN_FROZEN_V42_NATIVE_TEST_SOURCE_CHANGED')
    function = original.NativeExecutionV42Contracts.setUp
    if function.__code__.co_consts.count(ORIGINAL_CONFIGURATION) != 1:
        raise ValueError('UNKNOWN_LEGACY_FIXTURE_BINDING_SITE')
    code = function.__code__.replace(co_consts=tuple(
        LEGACY_CONFIGURATION if value == ORIGINAL_CONFIGURATION else value
        for value in function.__code__.co_consts))
    result = FunctionType(code,dict(function.__globals__),function.__name__,
                          function.__defaults__,function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


class LegacyNativeSourceV42Contracts(original.NativeExecutionV42Contracts):
    setUp = _legacy_setup()


class LegacyUnsupportedOriginalConfigurationV42(original.NativeExecutionV42Contracts):
    def test_original_importlib_configuration_remains_native_collection_unknown(self):
        self.assertEqual(self.environment['pytest_version'], '5.4.3')
        contract, authority = self.contract(
            'from alias import value\ndef test_old(): assert True\ndef test_new(): assert value()==0\n')
        with self.assertRaisesRegex(ValueError, 'UNKNOWN_COLLECTION_ERROR'):
            self.worker.collect(contract, authority, self.output(), policy=self.policy)
        self.assertEqual((self.repo/'pytest.ini').read_text(), ORIGINAL_CONFIGURATION)


def load_tests(loader, tests, pattern):
    return unittest.TestSuite((LegacyNativeSourceV42Contracts(
        'test_actual_link_import_failure_success_and_independent_reexecution'),
        LegacyNativeSourceV42Contracts('test_alias_candidate_is_refused_before_native_warrant'),
        LegacyUnsupportedOriginalConfigurationV42(
            'test_original_importlib_configuration_remains_native_collection_unknown')))


if __name__ == '__main__':
    unittest.main()
