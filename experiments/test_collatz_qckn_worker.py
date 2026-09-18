from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import collatz_qckn_worker as worker


class QCKNControlledWorkerTests(unittest.TestCase):
    def _bank(self, rows):
        f=tempfile.NamedTemporaryFile("w",delete=False)
        payload={
            "version":"collatz-endpoint-bank-v1",
            "endpoints":{str(k):v for k,v in rows.items()},
        }
        f.write(json.dumps(payload,sort_keys=True,separators=(",",":"))+"\n")
        f.close()
        return f.name

    def test_known_live_two_replay_source_reuses_supplied_bank(self):
        path=self._bank({157_755_113:105})
        bank=worker.load_bank(path,1000)
        result=worker.audit(5_054_715,5_054_715,128,1000,bank)
        self.assertEqual(result["counts"].get("live_two_replay"),1)
        self.assertEqual(result["counts"].get("compiled_reuse_hit"),1)
        self.assertEqual(result["candidate_acquisitions"],[])
        self.assertEqual(result["unresolved"],[])

    def test_same_source_acquires_candidate_when_bank_is_empty(self):
        path=self._bank({})
        bank=worker.load_bank(path,1000)
        result=worker.audit(5_054_715,5_054_715,128,1000,bank)
        self.assertEqual(result["counts"].get("live_two_replay"),1)
        self.assertEqual(result["counts"].get("candidate_verifier_calls"),1)
        self.assertEqual(len(result["candidate_acquisitions"]),1)
        row=result["candidate_acquisitions"][0]
        self.assertEqual(row["endpoint"],157_755_113)
        self.assertEqual(row["steps_to_one"],105)
        self.assertEqual(result["unresolved"],[])

    def test_bad_bank_evidence_is_rejected(self):
        path=self._bank({157_755_113:104})
        with self.assertRaisesRegex(ValueError,"bank verification failed"):
            worker.load_bank(path,1000)


if __name__=="__main__":
    unittest.main()
