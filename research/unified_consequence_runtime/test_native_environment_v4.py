"""Preimplementation contracts for the metadata-only V4 binding."""
import hashlib
import importlib
import types
import unittest
from pathlib import Path

from . import native_environment_v3 as frozen_environment
from . import native_environment_selection_v3 as frozen_selection
from . import native_execution_v3 as frozen_execution


class EnvironmentBindingV4(unittest.TestCase):
    def test_original_modules_and_all_bound_function_globals_remain_unmodified(self):
        before = {name: id(value) for name, value in vars(frozen_environment).items()}
        current = importlib.import_module(__package__ + '.native_environment_v4')
        self.assertEqual(before, {name: id(value) for name, value in vars(frozen_environment).items()})
        self.assertIs(frozen_environment.selection, frozen_selection)
        self.assertIs(current.execution, frozen_execution)
        self.assertIs(current.provision.__code__, frozen_environment.provision.__code__)
        self.assertIsNot(current.provision.__globals__, frozen_environment.provision.__globals__)
        self.assertIs(current.provision.__globals__['selection'], current.selection)
        self.assertTrue(current.selection.__name__.endswith('native_environment_selection_v4'))
        self.assertIs(current.provision.__globals__['bound_provision'].__globals__, current.provision.__globals__)

    def test_versioned_selector_preserves_original_derivation_bytecode_in_private_globals(self):
        current = importlib.import_module(__package__ + '.native_environment_selection_v4')
        self.assertIs(current.derive_constraints.__code__, frozen_selection.derive_constraints.__code__)
        self.assertIsNot(current.derive_constraints.__globals__, frozen_selection.derive_constraints.__globals__)
        self.assertIs(current.select_profile.__code__, frozen_selection.select_profile.__code__)
        self.assertIs(current.select_profile.__globals__['derive_constraints'], current.derive_constraints)
        self.assertEqual(current.CONSTRAINT_SCHEMA, 'UDM_NATIVE_ENVIRONMENT_CONSTRAINTS_V4')
        self.assertEqual(current.SELECTION_SCHEMA, 'UDM_NATIVE_ENVIRONMENT_SELECTION_V4')
        self.assertEqual(current.CATALOG_SCHEMA, frozen_selection.CATALOG_SCHEMA)
        self.assertEqual(hashlib.sha256(Path(frozen_selection.__file__).read_bytes()).hexdigest(),
                         '5a8cbc4a8f3dfa7969516f4bf0a39d3f7720789b764d83764112234834f3af3b')


if __name__ == '__main__':
    unittest.main()
