"""Frozen v7 typed-source V104/MSI bridge acceptance suite (authored before implementation).

Synthetic source-native contracts here prove interface behavior only; they do
NOT establish prospective unfamiliar-source G2. The separate fixed Click,
Tenacity and Packaging pool is frozen in typed-v104-v7/PROTOCOL.json.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from . import typed_source_inventory_v5 as typed
from . import typed_native_authority_v6 as native
from . import typed_v104_msi_bridge_v7 as v7


def git(repo, *args):
    return subprocess.check_output(["git","-C",str(repo),*args],text=True,
                                   stderr=subprocess.PIPE).strip()


class FrozenV7TypedV104Bridge(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="v7-frozen-")
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve()
        self.repo=self.root/"original"
        self.repo.mkdir()
        git(self.repo,"init","-q")
        git(self.repo,"config","user.name","V7 Frozen")
        git(self.repo,"config","user.email","v7@example.invalid")
        (self.repo/"src/pkg").mkdir(parents=True)
        (self.repo/"tests").mkdir()
        (self.repo/"docs").mkdir()
        (self.repo/"docs/intro.rst").write_text("source verified\n")
        (self.repo/"README.rst").symlink_to("docs/intro.rst")
        (self.repo/"src/pkg/__init__.py").write_text("def value():\n    return 0\n")
        (self.repo/"tests/test_pkg.py").write_text(
            "from pkg import value\n"
            "def test_old(): assert value() == 0\n")
        git(self.repo,"add","-A")
        git(self.repo,"update-index","--add","--cacheinfo",
            "160000,"+"a"*40+",vendor/opaque")
        git(self.repo,"commit","-qm","frozen baseline")
        self.base=git(self.repo,"rev-parse","HEAD")
        self.tests=("from pkg import value\n"
            "def test_old(): assert True\n"
            "def test_future(): assert value() == 1\n").encode()
        # Head production is unavailable to adapter; this artifact is only
        # independently supplied author-test bytes with a Git-blob binding.
        self.test_oid=git(self.repo,"hash-object","-w","--stdin") if False else None
        self.test_oid=subprocess.check_output(["git","-C",str(self.repo),"hash-object",
            "-w","--stdin"],input=self.tests).decode().strip()
        self.test_row={"path":"tests/test_pkg.py","git_oid":self.test_oid,
                       "sha256":hashlib.sha256(self.tests).hexdigest(),
                       "bytes":self.tests.hex()}
        self.msi=Path(__file__).resolve().parents[2]/"components/msi"
        self.triskelion=Path(__file__).resolve().parents[2]/"components/triskelion"
        # Workflow supplies these original method source checkouts. Individual
        # local tests of syntactic admission do not depend on these checkouts.
        import os
        self.msi=Path(os.environ.get("UDM_V7_MSI",self.msi))
        self.triskelion=Path(os.environ.get("UDM_V7_TRISKELION",self.triskelion))

    def test_A01_author_test_source_is_derived_not_user_chosen(self):
        rows=v7.changed_author_assertions(self.repo,self.base,[self.test_row])
        self.assertEqual(rows,["tests/test_pkg.py::test_future"])
        self.assertNotIn("tests/test_pkg.py::test_old",rows)

    def test_A02_wrong_original_author_blob_digest_refused(self):
        for field,value in [("git_oid","b"*40),("sha256","f"*64),("path","src/pkg/__init__.py")]:
            row=dict(self.test_row,**{field:value})
            with self.subTest(field=field),self.assertRaises(ValueError):
                v7.changed_author_assertions(self.repo,self.base,[row])

    def test_A03_typed_candidate_commit_preserves_gitlink_and_symlink(self):
        record=v7.construct_candidate(self.repo,self.base,[self.test_row],
                                      {"replacements":[]},self.root/"candidate-a")
        self.assertEqual(record["status"],"SOURCE_BOUND_CANDIDATE_COMMIT_NO_WARRANT")
        manifest=typed.snapshot(self.repo,record["candidate_commit"])
        self.assertEqual(manifest["counts"],{"regular":4,"symlink":1,"gitlink":1})
        self.assertEqual(manifest["links"][0]["resolution"],"INTERNAL_REGULAR_FILE")
        self.assertEqual(manifest["gitlinks"][0]["status"],"OPAQUE_NOT_NATIVE_EXECUTION_AUTHORITY")

    def test_A04_candidate_cannot_mutate_test_authority_or_wrong_production(self):
        for path in ("tests/test_pkg.py","README.rst","vendor/opaque","outside.py"):
            with self.subTest(path=path),self.assertRaises(ValueError):
                v7.construct_candidate(self.repo,self.base,[self.test_row],
                    {"replacements":[{"path":path,
                        "original_sha256":"0"*64,"replacement":"return 1\n"}]},
                    self.root/("bad"+str(len(path))+path.replace("/","-")))

    def test_A05_wrong_original_production_digest_refused(self):
        with self.assertRaises(ValueError):
            v7.construct_candidate(self.repo,self.base,[self.test_row],
                {"replacements":[{"path":"src/pkg/__init__.py",
                    "original_sha256":"0"*64,
                    "replacement":"def value(): return 1\n"}]},self.root/"bad-hash")

    def test_A06_independently_derived_protected_fail_baseline(self):
        row=v7.construct_candidate(self.repo,self.base,[self.test_row],
                    {"replacements":[]},self.root/"base-candidate")
        receipt=v7.native_profile(self.repo,row,self.root/"base-native",
                    interpreter=sys.executable,timeout=60)
        self.assertEqual(receipt["status"],"VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED")
        self.assertEqual(receipt["measurements"],[1,2])
        self.assertEqual(receipt["native_calls"],2)
        self.assertEqual(receipt["source_commit"],row["candidate_commit"])

    def test_A07_source_derived_v104_const_one_repair_is_independently_native(self):
        rows=v7.catalog_v104_typed(self.repo,self.base,["src/pkg/__init__.py"],
                                 self.triskelion,self.msi, cap=64)
        self.assertTrue(rows["rows"])
        repair=next((r for r in rows["rows"] if
                     "return 1" in r["candidate"]["replacements"][0]["replacement"]),None)
        self.assertIsNotNone(repair,"Original V104 must emit a source-defined repair")
        build=v7.construct_candidate(self.repo,self.base,[self.test_row],
                    repair["candidate"],self.root/"repaired-candidate")
        receipt=v7.native_profile(self.repo,build,self.root/"repaired-native",
                                  interpreter=sys.executable,timeout=60)
        self.assertEqual(receipt["status"],"VERIFIED_REPEATED_PASS_SCOPED_NATIVE")
        self.assertEqual(receipt["measurements"],[0,2])
        self.assertEqual(receipt["native_calls"],2)

    def test_A08_original_MSI_36_policies_and_cold_order_are_retained(self):
        rows=v7.catalog_v104_typed(self.repo,self.base,["src/pkg/__init__.py"],
                                 self.triskelion,self.msi,cap=64)
        self.assertEqual(len(rows["orders"]),37)
        self.assertEqual(rows["orders"]["COLD_V104_ORDER"],
                         [x["id"] for x in rows["rows"]])
        self.assertEqual(rows["source"]["v104_language"],"ORIGINAL_PINNED_V104")
        self.assertEqual(rows["source"]["msi_policy"],"ORIGINAL_PINNED_MSI_V10")

    def test_A09_unknown_native_call_does_not_map_to_failure(self):
        with self.assertRaises(ValueError):
            v7.verified_profiles([{"candidate":"cold","future":"taskA",
                "status":"UNKNOWN_NATIVE_COLLECTION","native_calls":1}],
                ("cold",),("taskA",))

    def test_A10_source_bound_msi_pareto_works_on_native_measurements(self):
        from .developmental_choice import choose_verified_profiles
        positives=[
            {"candidate":"COLD","future":"A","status":"VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED","measurements":[1,2],"native_calls":2,"source_commit":"a"*40,"native_evidence_sha256":"0"*64},
            {"candidate":"COLD","future":"B","status":"VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED","measurements":[1,2],"native_calls":2,"source_commit":"b"*40,"native_evidence_sha256":"1"*64},
            {"candidate":"WARM","future":"A","status":"VERIFIED_REPEATED_PASS_SCOPED_NATIVE","measurements":[0,2],"native_calls":2,"source_commit":"a"*40,"native_evidence_sha256":"2"*64},
            {"candidate":"WARM","future":"B","status":"VERIFIED_REPEATED_PASS_SCOPED_NATIVE","measurements":[0,2],"native_calls":2,"source_commit":"b"*40,"native_evidence_sha256":"3"*64}
        ]
        # This is a deterministic test of profile-binding + original source
        # Pareto implementation, not new native evidence/scientific authority.
        carrier=v7.verified_profiles(positives,("COLD","WARM"),("A","B"))
        self.assertEqual(carrier["profiles"]["WARM"]["B"],[0,2])
        self.assertEqual(carrier["profiles"]["COLD"]["B"],[1,2])
        record=v7.original_msi_decision(carrier,self.repo,scope={
            "protocol_binding":"a"*64,
            "catalog_sha256":"b"*64,
            "source_binding":"c"*64,
            "budget":8})
        self.assertEqual(record["choice"]["status"],"AUTHORIZED_REPAIR")
        self.assertEqual(record["choice"]["selected"],"WARM")
        self.assertEqual(record["scientific_promotion"],"NONE")

    def test_A11_missing_compared_candidates_never_infer_unique_g2(self):
        with self.assertRaises(ValueError):
            v7.verified_profiles([{"candidate":"ONLY","future":"A",
                "status":"VERIFIED_REPEATED_PASS_SCOPED_NATIVE",
                "measurements":[0,2],"native_calls":2,
                "source_commit":"a"*40,"native_evidence_sha256":"0"*64}],
                ("ONLY","MISSING"),("A",))

    def test_A12_independent_native_withdrawal_reverts_to_failing_source(self):
        repaired={"replacements":[{"path":"src/pkg/__init__.py",
            "original_sha256":hashlib.sha256(
                (self.repo/"src/pkg/__init__.py").read_bytes()).hexdigest(),
            "replacement":"def value():\n    return 1\n"}]}
        row=v7.construct_candidate(self.repo,self.base,[self.test_row],repaired,
                                   self.root/"positive")
        pos=v7.native_profile(self.repo,row,self.root/"posnative",
                              interpreter=sys.executable,timeout=60)
        self.assertEqual(pos["status"],"VERIFIED_REPEATED_PASS_SCOPED_NATIVE")
        cold=v7.construct_candidate(self.repo,self.base,[self.test_row],
                                    {"replacements":[]},self.root/"ablation")
        neg=v7.native_profile(self.repo,cold,self.root/"negnative",
                              interpreter=sys.executable,timeout=60)
        self.assertEqual(neg["status"],"VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED")
        self.assertNotEqual(row["candidate_commit"],cold["candidate_commit"])

if __name__=="__main__":
    unittest.main()
