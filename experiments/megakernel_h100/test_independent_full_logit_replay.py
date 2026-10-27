"""CPU-only full 128256-element BF16 replay and corruption controls."""
from array import array
import base64, copy, hashlib, struct, sys, unittest, zlib
from independent_full_logit_replay import audit, decode, N
from test_independent_consequence_assurance import fixture

def exact_bf16_payload():
    if sys.byteorder!="little": raise RuntimeError("test assumes x86 little endian")
    vals=array("H",[0])*N
    for i,bits in enumerate((0x3f80,0x4000,0x4040,0x4080,0x40a0)):
        vals[i]=bits
    raw=vals.tobytes()
    blob=zlib.compress(raw,6)
    return {"dtype":"bf16-le","elements":N,"raw_bytes":len(raw),
            "raw_sha256":hashlib.sha256(raw).hexdigest(),
            "compressed_bytes":len(blob),
            "zlib_base64":base64.b64encode(blob).decode("ascii")}

def authentic_shape_sample():
    report=fixture()
    rec=exact_bf16_payload()
    for check in report["checks"].values():
        check["raw_logits_bf16"]={"reference":copy.deepcopy(rec),"native":copy.deepcopy(rec)}
        check["fields"]["logits"]["max_abs_diff"]=0.0
        c=check["logit_choice"]
        c.update({"reference_top1":4,"native_top1":4,"top1_equal":True,
                  "reference_top1_margin":1.0,"native_top1_margin":1.0,
                  "reference_top5":[4,3,2,1,0],"native_top5":[4,3,2,1,0],
                  "candidate_logits":[{"index":i,"reference":float(i+1),"native":float(i+1)}
                                      for i in range(5)]})
    return report

class ReplayTests(unittest.TestCase):
    def setUp(self): self.report=authentic_shape_sample()

    def test_recompute_all_six_full_vectors(self):
        value=audit(self.report)
        self.assertEqual(value["cases_checked"],6)
        self.assertEqual(value["pairs_of_logits_replayed"],6*N)
        self.assertEqual(value["top1_agreements"],6)
        self.assertEqual(value["sufficient_ranking_margins"],6)
        self.assertEqual(value["exhaustive_strict_winner_certificates"],6)
        self.assertTrue(all(x["exhaustive_winner_gap"] > 0 for x in value["cases"].values()))
        self.assertIn("NOT_INDEPENDENT_GPU",value["status"])

    def test_mutated_payload_hash_rejected(self):
        self.report["checks"]["seed0_rr"]["raw_logits_bf16"]["native"]["raw_sha256"]="f"*64
        with self.assertRaises(ValueError): audit(self.report)

    def test_truncated_encoded_vector_rejected(self):
        self.report["checks"]["seed0_rr"]["raw_logits_bf16"]["native"]["zlib_base64"]="AA=="
        with self.assertRaises(ValueError): audit(self.report)

    def test_forged_max_abs_error_rejected(self):
        self.report["checks"]["seed0_rr"]["fields"]["logits"]["max_abs_diff"]=0.125
        with self.assertRaises(ValueError): audit(self.report)

    def test_forged_top_token_rejected(self):
        self.report["checks"]["seed7_dag"]["logit_choice"]["reference_top1"]=3
        with self.assertRaises(ValueError): audit(self.report)

    def test_unbounded_encoded_payload_rejected(self):
        rec=exact_bf16_payload()
        rec["zlib_base64"]="A"*365001
        with self.assertRaises(ValueError): decode(rec)

    def test_nonfinite_bf16_rejected(self):
        rec=exact_bf16_payload()
        bits=array("H",[0])*N
        bits[0]=0x7f80
        raw=bits.tobytes()
        blob=zlib.compress(raw)
        rec.update({"raw_sha256":hashlib.sha256(raw).hexdigest(),
                    "compressed_bytes":len(blob),
                    "zlib_base64":base64.b64encode(blob).decode("ascii")})
        with self.assertRaises(ValueError): decode(rec)

if __name__=="__main__": unittest.main()
