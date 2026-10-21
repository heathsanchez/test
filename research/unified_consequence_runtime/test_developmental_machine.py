"""Causal contract tests against original executable sources and native checks."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

class DevelopmentalMachineTests(unittest.TestCase):
    def setUp(self):
        name = 'research.unified_consequence_runtime.developmental_machine'
        self.assertIsNotNone(importlib.util.find_spec(name), 'live executable runtime missing')
        from research.unified_consequence_runtime.developmental_machine import Machine
        self.Machine = Machine
        self.assets = Path(os.environ.get('UDM_ASSETS', '/workspace/archaeology/depth5-original'))
        self.components = Path(os.environ.get('UDM_COMPONENTS', '/workspace/components'))
        self.evaluator = Path(os.environ.get('UDM_EVALUATOR', '/workspace/repos/webarena-verified'))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.machine = Machine(self.components, Path(self.temp.name), self.evaluator,
                               self.assets / 'config.json')

    def tasks(self, *ids):
        return [t for t in json.loads((self.assets / 'full_no_eval.json').read_text())
                if t['task_id'] in ids]

    def test_scope_rejects_future_task_and_evaluation_leak(self):
        candidate = self.machine.acquire_grouping(self.tasks(63)[0],
                                                 json.loads((self.assets/'e_obs.json').read_text()))
        with self.assertRaises(ValueError):
            self.machine.execute(candidate, self.tasks(168)[0])
        leaked = self.tasks(62)[0] | {'eval': {'reference': 'forged'}}
        with self.assertRaises(ValueError):
            self.machine.execute(candidate, leaked)

    def test_withdrawal_removes_route_descendants_and_restart_preserves_independent(self):
        m = self.machine
        grouping = m.acquire_grouping(self.tasks(63)[0], json.loads((self.assets/'e_obs.json').read_text()))
        independent = m.activate_stars(json.loads((self.assets/'d_obs.json').read_text()),
                                       json.loads((self.assets/'d_binding.json').read_text()), self.tasks(169)[0])
        _, consequence = m.execute(grouping, self.tasks(62)[0])
        _, other = m.execute(independent, self.tasks(172)[0])
        old_ids = set(m.mt.ids(m.log))
        m.withdraw(grouping, 'controlled exact source support withdrawal')
        self.assertNotIn(consequence, m.mt.live_ids(m.log))
        self.assertIn(other, m.mt.live_ids(m.log))
        with self.assertRaises(PermissionError):
            m.execute(grouping, self.tasks(62)[0])
        reopened = self.Machine(self.components, Path(self.temp.name), self.evaluator,
                                self.assets/'config.json')
        self.assertFalse(reopened.applicable(grouping, self.tasks(62)[0]))
        self.assertTrue(reopened.applicable(independent, self.tasks(172)[0]))
        restored = reopened.acquire_grouping(self.tasks(63)[0],
                                              json.loads((self.assets/'e_obs.json').read_text()),
                                              supersedes=grouping)
        self.assertNotEqual(restored, grouping)
        response, new_consequence = reopened.execute(restored, self.tasks(62)[0])
        self.assertEqual(response['status'], 'SUCCESS')
        self.assertIn(new_consequence, reopened.mt.live_ids(reopened.log))
        self.assertTrue(old_ids <= set(reopened.mt.ids(reopened.log)))
        self.assertEqual(set(reopened.mt.live_ids(reopened.log)), reopened.flash_live_ids())
        from research.unified_consequence_runtime.qualify_developmental_machine import run_cold_replay
        root = Path(self.temp.name)
        spec = {'components':str(self.components), 'state':str(root),
                'evaluator':str(self.evaluator), 'config':str(self.assets/'config.json'),
                'assets':str(self.assets), 'withdrawn':grouping,
                'capabilities':{'grouping':restored,'stars':independent}}
        (root/'replay-spec.json').write_text(json.dumps(spec))
        result = run_cold_replay(root/'replay-spec.json', root/'cold.json')
        self.assertEqual(result['status'], 'PASS')
        self.assertTrue(result['withdrawn_generation_inactive'])
        self.assertEqual(len(result['outcomes']),6)

if __name__ == '__main__':
    unittest.main()
