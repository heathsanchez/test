"""Fail-closed typed routing checks; scientific results come from native qualification."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


class V54RuntimeTests(unittest.TestCase):
    def setUp(self):
        name='research.unified_consequence_runtime.v54_runtime'
        self.assertIsNotNone(importlib.util.find_spec(name),'V54 executable route missing')
        from research.unified_consequence_runtime.developmental_machine import Machine
        from research.unified_consequence_runtime.v54_runtime import V54Runtime
        from research.unified_consequence_runtime.v54_source import OriginalV54
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        source=Path(os.environ.get('V54_SOURCE','/workspace/repos/triskelion'))
        worlds=Path(os.environ.get('V54_WORLDS','/workspace/v54-worlds'))
        session=OriginalV54(source,{n:worlds/n for n in ('django','requests','rich')},root/'source')
        machine=Machine(Path(os.environ.get('UDM_COMPONENTS','/workspace/components')),root/'state',
            Path(os.environ.get('UDM_EVALUATOR','/workspace/repos/webarena-verified')),
            Path(os.environ.get('UDM_ASSETS','/workspace/archaeology/depth5-original'))/'config.json')
        self.runtime=V54Runtime(machine,session,source,worlds,Path(os.environ.get('V54_PYTHON','/workspace/v54-venv/bin/python')))

    def test_unacquired_operator_cannot_be_admitted(self):
        with self.assertRaises(PermissionError):
            self.runtime.admit_operator('O1',{'kind':'TOKEN_REWRITE','src':'fake','dst':'answer'})

    def test_capability_cannot_grant_external_authority(self):
        self.assertEqual(self.runtime.authority_ceiling['external_effects'],'NONE')
        self.assertEqual(self.runtime.authority_ceiling['reference_monitor'],'UNKNOWN_NONBYPASSABILITY')
        self.assertNotIn('executable_capability',[n.kind for n in self.runtime.machine.log])

    def test_selected_virtual_environment_interpreter_is_preserved(self):
        expected=Path(os.environ.get('V54_PYTHON','/workspace/v54-venv/bin/python')).absolute()
        self.assertEqual(self.runtime.native_python,expected)

    def test_missing_ancestor_rejected_before_native_execution(self):
        with self.assertRaises((PermissionError,KeyError,StopIteration,ValueError)):
            self.runtime.apply('missing-capability')


if __name__=='__main__':unittest.main()
