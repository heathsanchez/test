"""Post-freeze interface regression from the first committed V42 gate refusal."""
import json
import os
from pathlib import Path
import sys
import unittest

from . import native_environment_v42 as environment
from . import native_execution_v42 as execution
from . import native_execution_v3 as previous


class NativeEnvironmentV42InterfaceContracts(unittest.TestCase):
    def test_original_environment_helper_has_unchanged_frozen_dependency(self):
        self.assertIs(getattr(execution, 'frozen', None), previous.frozen)

    def test_real_runtime_freeze_and_independent_validation_use_selected_interpreter(self):
        path = os.environ.get('UDM_NATIVE_V42_INTERPRETER', sys.executable)
        record = environment.freeze_runtime(path)
        version = '.'.join(str(v) for v in record['identity']['version_info'][:3])
        profile = {'python_version': version,
                   'python_implementation': record['identity']['implementation']}
        self.assertEqual(environment.validate_runtime(profile, record), record['identity'])
        self.assertEqual(execution.runtime_identity(path), record['identity'])
        self.assertTrue(record['stdlib_files'])


if __name__ == '__main__':
    unittest.main()
