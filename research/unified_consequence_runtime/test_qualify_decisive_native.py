"""Causal promotion rejects incomplete or epistemically unresolved controls."""
import unittest
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from .qualify_decisive_native import verified_failed_prefix,copy_state
from .decisive_native_verify import fingerprint
from .developmental_machine import Machine


class CausalPrefixContracts(unittest.TestCase):
    def test_only_complete_independently_failed_native_prefix_can_promote(self):
        records={key:{'status':'UNKNOWN_NATIVE_ERROR' if key=='u' else 'FAIL_NATIVE','candidate':{'fixture':key}} for key in ('a','b','u')}
        orders=lambda keys:[fingerprint(records[key]['candidate']) for key in keys]
        machine=SimpleNamespace(get=lambda key:records[key])
        with patch('research.unified_consequence_runtime.qualify_decisive_native.checked_native_receipt',
                   side_effect=lambda record,machine:record):
            self.assertTrue(verified_failed_prefix(machine,{'winner':None,'attempts':['a','b']},orders(['a','b'])+['unexamined'],2))
            self.assertFalse(verified_failed_prefix(machine,{'winner':None,'attempts':['a']},orders(['a','b'])+['unexamined'],2))
            self.assertFalse(verified_failed_prefix(machine,{'winner':None,'attempts':['a','u']},orders(['a','u']),2))
            self.assertFalse(verified_failed_prefix(machine,{'winner':'b','attempts':['a','b']},orders(['a','b']),2))
            self.assertFalse(verified_failed_prefix(machine,{'winner':None,'attempts':[]},[],2))
            self.assertFalse(verified_failed_prefix(machine,{'winner':None,'attempts':['b','a']},orders(['a','b']),2))

    def test_a_forged_native_failure_is_not_a_control(self):
        machine=SimpleNamespace(get=lambda key:{'status':'FAIL_NATIVE','candidate':{}})
        with patch('research.unified_consequence_runtime.qualify_decisive_native.checked_native_receipt',
                   side_effect=ValueError('forged raw native packet')):
            with self.assertRaises(ValueError):
                verified_failed_prefix(machine,{'winner':None,'attempts':['forged']},[fingerprint({})],1)


class QualifiedStateBootstrapContracts(unittest.TestCase):
    def test_original_246_record_publications_reload_without_retargeting_validator(self):
        with tempfile.TemporaryDirectory(prefix='udm-qualified-bootstrap-') as folder:
            root=Path(folder);copy_state(root)
            original=(root/'state/metatron-ledger.jsonl').read_bytes()
            components=Path(os.environ.get('UDM_COMPONENTS','/workspace/components'))
            machine=Machine(components,root/'state',components/'evaluator',root/'unused-config.json')
            self.assertEqual(len(machine.log),246)
            self.assertEqual((root/'state/metatron-ledger.jsonl').read_bytes(),original)
            self.assertEqual(set(machine.mt.live_ids(machine.log)),machine.flash_live_ids())


if __name__=='__main__':unittest.main()
