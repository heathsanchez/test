"""Adversarial receipt admission: no publisher-status trust or false promotions."""
import copy
import io
import json
from pathlib import Path
import unittest
import zipfile

import consume as C

HERE=Path(__file__).resolve().parent
PIN="1374343177ac75b0cfbfa154a87fafc26d91fe92"

class RecipientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(HERE/"policy.json").read_bytes()
        cls.p=C.policy_valid(cls.raw,PIN)
        cls.b={
            a["name"]:(HERE/"inputs"/(a["name"]+".zip")).read_bytes()
            for a in cls.p["artifacts"]
        }
        cls.z=C.archive(cls.b["native-differential"],
                        cls.p["artifacts"][0]["sha256"])
        cls.g=C.archive(cls.b["native-protected-go-test"],
                        cls.p["artifacts"][1]["sha256"])
        cls.opa=C.strict_json(cls.z.read("opa.json"))
        cls.gojq=C.strict_json(cls.z.read("gojq.json"))
        cls.old=C.strict_json(cls.g.read("protected_conflict_report.json"))
        cls.byid={x["id"]:x for x in cls.p["sources"]}

    @classmethod
    def original_files(cls,e,src,revision):
        label="original-go-test-base" if revision=="source_base" else "original-go-test-head"
        return (HERE/"inputs"/(label+".go")).read_bytes()

    def rejects(self,why,f,*args,**kwargs):
        with self.assertRaises(C.Refused) as caught:
            f(*args,**kwargs)
        self.assertIn(why,str(caught.exception))

    def test_authentic_all_three_native_receipts(self):
        r=C.reconcile(self.raw,PIN,self.b,source_reader=self.original_files)
        self.assertEqual(r["status"],
                         "WARRANTED_BOUNDED_HISTORICAL_CONSEQUENCE_RECONCILIATION")
        self.assertEqual([x["kind"] for x in r["receipts"]],
                         ["EXECUTABLE_IMPLEMENTATION_DISAGREEMENT",
                          "EXECUTABLE_IMPLEMENTATION_DISAGREEMENT",
                          "PROTECTED_OLD_TEST_CONTRADICTION"])
        self.assertEqual(r["action_authority"],"NONE")
        self.assertFalse(r["live_check_published"])
        self.assertEqual([x["base_mismatch_count"] for x in r["receipts"][:2]],
                         [2,14])
        self.assertEqual(r["receipts"][2]["native_logs_replayed"],35)

    def test_policy_is_independently_pinned(self):
        self.rejects("EXTERNAL_POLICY_PIN_MISMATCH",C.policy_valid,
                     self.raw+b" ",PIN)
        self.rejects("EXTERNAL_POLICY_PIN_MISMATCH",C.policy_valid,
                     self.raw,"0"*40)

    def test_original_archive_byte_mutation(self):
        modified={**self.b,"native-differential":
                  self.b["native-differential"][:-4]+b"0000"}
        self.rejects("ARCHIVE_DIGEST_NOT_AUTHORIZED",C.reconcile,
                     self.raw,PIN,modified,source_reader=self.original_files)

    def test_unapproved_subject_revision(self):
        o=copy.deepcopy(self.opa)
        p=copy.deepcopy(self.byid["opa-cross-backend"])
        p["source_base"]="0"*40
        self.rejects("SOURCE_SHA_CHANGED",C.diff_obs,o,p)

    def test_fake_producer_success_with_no_native_witness(self):
        o=copy.deepcopy(self.opa)
        for x in o["observations"]:
            if x["base_reference"]=="DIFFERENT":
                x["base_reference"]="EQUAL"
        self.rejects("FORGED_DIFFERENTIAL_CLASSIFICATION",C.diff_obs,
                     o,self.byid["opa-cross-backend"])

    def test_fake_counts_deny_credit(self):
        o=copy.deepcopy(self.gojq)
        o["counts"]["mismatches_repaired_at_head"]=50
        self.rejects("COUNTS_NOT_RECOMPUTED",C.diff_obs,
                     o,self.byid["gojq-cross-backend"])

    def test_minimal_witness_must_be_real(self):
        o=copy.deepcopy(self.opa)
        o["minimal_witness"]["input"]={"not":"the original input"}
        self.rejects("WITNESS_OR_NEGATIVE_NOT_IN_NATIVE_CASES",
                     C.diff_obs,o,self.byid["opa-cross-backend"])

    def test_reference_ablation_never_promotes(self):
        x=C.strict_json(self.z.read("gojq-ablation.json"))
        x["result"]="WARRANTED_BOUNDED_NATIVE_DIFFERENTIAL_REPAIRED"
        class Archive:
            def read(self,_):
                return json.dumps(x).encode()
        self.rejects("REFERENCE_REMOVAL_WOULD_FALSELY_PROMOTE",
                     C.diff_controls,Archive(),self.gojq,["gojq-ablation.json"])

    def test_withdrawal_does_not_erase_history(self):
        x=C.strict_json(self.z.read("gojq-withdrawal.json"))
        x["observations"][0]["arms"]["base"]["value"]=["fake"]
        class Archive:
            def read(self,_):
                return json.dumps(x).encode()
        self.rejects("WITHDRAWAL_ERASED_HISTORY_OR_STILL_WARRANTED",
                     C.diff_controls,Archive(),self.gojq,["gojq-withdrawal.json"])

    def test_old_test_success_status_not_authority(self):
        x=copy.deepcopy(self.old)
        x["native_package_results"]["./internal/backend/wasm"]["head_full_suite_exit"]=0
        self.rejects("CAUSAL_GATE_FAIL",C.protected_obs,x,self.g,
                     self.byid["howlframe-protected-old-test"],
                     source_reader=self.original_files)

    def test_protected_test_original_bytes_not_authorized(self):
        def fake_source(e,src,rev):
            return b"func TestFake(t *testing.T) {}\n"
        self.rejects("ORIGINAL_UPSTREAM_TEST_FILE_PIN_FAIL",
                     C.protected_obs,self.old,self.g,
                     self.byid["howlframe-protected-old-test"],source_reader=fake_source)

    def test_missing_log_even_with_publisher_success_label(self):
        x=copy.deepcopy(self.old)
        x["status"]="WARRANTED_BOUNDED_ORIGINAL_TEST_CONTRACT_CONFLICT"
        x["steps"][0]["sha256"]="0"*64
        self.rejects("NATIVE_COMMAND_LOG_INTEGRITY_FAIL",
                     C.protected_obs,x,self.g,
                     self.byid["howlframe-protected-old-test"],
                     source_reader=self.original_files)

if __name__=="__main__":
    unittest.main()
