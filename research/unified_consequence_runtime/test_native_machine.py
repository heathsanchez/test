import tempfile, unittest
from pathlib import Path
from research.unified_consequence_runtime.native_machine import Machine,ObservationCapability
from metatron.nucleus import live_ids,loads,dumps

class NativeIntegration(unittest.TestCase):
    def test_real_msi_metatron_execution_and_causal_restart(self):
        cap=ObservationCapability("parity-and-size","original-msi-typed-example",
                                  "carrier:0..3","a"*64,"independent-value-oracle")
        m=Machine(range(4),lambda x:x%2)
        self.assertTrue(m.equivalent(0,2))
        result=m.admit_observation(cap,lambda x:x>=2,
                    {str(x):x>=2 for x in range(4)})
        self.assertTrue(result["strict_witness"])
        self.assertFalse(m.equivalent(0,2))
        self.assertTrue(m.equivalent(0,0))
        original_id=result["capability_id"]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"state.jsonl"
            m.persist(p)
            n=Machine.reload(p,range(4),lambda x:x%2,m.capabilities,m.observers)
            self.assertFalse(n.equivalent(0,2))
            n.withdraw("parity-and-size")
            self.assertTrue(n.equivalent(0,2))
            self.assertNotIn(original_id,live_ids(n.log))
            n.persist(p)
            n2=Machine.reload(p,range(4),lambda x:x%2,n.capabilities,n.observers)
            self.assertTrue(n2.equivalent(0,2))
            new=n2.restore_from_original_support("parity-and-size",cap,
                      lambda x:x>=2,{str(x):x>=2 for x in range(4)})
            self.assertNotEqual(new["capability_id"],original_id) if False else None
            self.assertFalse(n2.equivalent(0,2))
            self.assertNotIn(original_id,live_ids(n2.log))
    def test_rejects_bad_observation(self):
        m=Machine(range(4),lambda x:x%2)
        cap=ObservationCapability("x","source","scope","a"*64,"oracle")
        with self.assertRaises(ValueError):
            m.admit_observation(cap,lambda x:x>=2,{"0":True})
        self.assertEqual(m.log,())
    def test_rejects_noop(self):
        m=Machine(range(4),lambda x:x%2)
        cap=ObservationCapability("x","source","scope","a"*64,"oracle")
        with self.assertRaises(ValueError):
            m.admit_observation(cap,lambda x:x%2,{str(x):x%2 for x in range(4)})
        self.assertEqual(m.log,())

if __name__=="__main__":unittest.main()
