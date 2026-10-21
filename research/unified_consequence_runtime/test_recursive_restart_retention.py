"""Real Metatron/FLASH separate-process persistence regression, not science."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from research.unified_consequence_runtime.developmental_machine import Machine
from research.unified_consequence_runtime import qualify_recursive_frontier as q


class RestartRetentionTests(unittest.TestCase):
    def test_child_consequence_survives_parent_continuation(self):
        with tempfile.TemporaryDirectory() as folder:
            state=Path(folder)/'state'
            components=Path(os.environ.get('UDM_COMPONENTS','/workspace/components'))
            parent=Machine(components,state,Path(folder)/'evaluator',Path(folder)/'config')
            source=parent.append('fixture_source',{'contract_test_only':True});parent.flush()
            prefix=(state/'metatron-ledger.jsonl').read_bytes()
            program='''import json,sys
from pathlib import Path
from research.unified_consequence_runtime.developmental_machine import Machine
m=Machine(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4]))
node=m.append('verified_consequence',{'contract_test_only':True},(sys.argv[5],));m.flush()
print(json.dumps({'consequence':node}))
'''
            raw=subprocess.check_output([sys.executable,'-B','-c',program,str(components),str(state),
                str(parent.evaluator),str(parent.config),source],text=True)
            child=json.loads(raw)
            parent=q.resume_after_restart(parent,child)
            later=parent.append('fixture_later',{'independent':True});parent.flush()
            loaded=Machine(components,state,parent.evaluator,parent.config)
            ids={node.id for node in loaded.log}
            self.assertIn(child['consequence'],ids)
            self.assertIn(later,ids)
            self.assertTrue((state/'metatron-ledger.jsonl').read_bytes().startswith(prefix))
            self.assertIn(child['consequence'],loaded.mt.live_ids(loaded.log))
            self.assertEqual(set(loaded.mt.live_ids(loaded.log)),loaded.flash_live_ids())

if __name__=='__main__':unittest.main()
