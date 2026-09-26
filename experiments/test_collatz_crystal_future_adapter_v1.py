import unittest
import collatz_crystal_future_adapter_v1 as adapter

class AdapterTests(unittest.TestCase):
    def test_reference_replay(self):
        result=adapter.reference_replay()
        self.assertTrue(result["checked"])
        self.assertEqual(result["scope"],"bounded")

if __name__=="__main__":
    unittest.main()
