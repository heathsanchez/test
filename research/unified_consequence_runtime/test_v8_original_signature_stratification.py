"""V8 pre-implementation contracts: source-pinned V104 signatures, NOT G2."""
import ast
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from . import qualify_v8_exposed_stratified_v104 as v8
from . import typed_source_inventory_v5 as typed
from . import typed_v104_msi_bridge_v7 as bridge

def git(path,*args):
    return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()

class FrozenV8ProgramWitnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="v8-frozen-stratification-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        self.repo=self.root/'source'
        self.repo.mkdir()
        git(self.repo,'init','-q')
        git(self.repo,'config','user.name','V8 frozen')
        git(self.repo,'config','user.email','v8@example.invalid')
        (self.repo/'pkg.py').write_text(
            'def transform(x, y):\n'
            '    while x:\n'
            '        if y:\n'
            '            return min(x,y)\n'
            '        x = x - 1\n'
            '    return 0\n')
        git(self.repo,'add','.')
        git(self.repo,'commit','-qm','freeze source')
        self.sha=git(self.repo,'rev-parse','HEAD')
        self.triskelion=Path(os.environ['UDM_V7_TRISKELION'])
        self.msi=Path(os.environ['UDM_V7_MSI'])

    def test_A01_all_candidates_original_signatures_with_frozen_scope(self):
        catalog=v8.stratified_catalog(self.repo,self.sha,['pkg.py'],
                                      self.triskelion,self.msi,cap=64)
        rows=catalog['rows']
        self.assertGreaterEqual(len(rows),5)
        self.assertEqual(len({r['id'] for r in rows}),len(rows))
        self.assertLessEqual(len(rows),64)
        self.assertTrue(all(ast.parse(r['candidate']['replacements'][0]['replacement']) for r in rows))
        self.assertEqual(len(catalog['orders']),37)
        self.assertTrue(all(set(order)=={r['id'] for r in rows} for order in catalog['orders'].values()))
        self.assertEqual(catalog['source']['v104_language'],'ORIGINAL_PINNED_V104')
        self.assertEqual(catalog['source']['msi_policy'],'ORIGINAL_PINNED_MSI_V10')
        self.assertEqual(catalog['source']['search_variant'],'ROUND_ROBIN_ONE_PER_ORIGINAL_SIGNATURE')
        self.assertGreater(len({tuple(r['builder']) for r in rows}),1)

    def test_A02_source_mutation_changes_candidate_source_binding(self):
        first=v8.stratified_catalog(self.repo,self.sha,['pkg.py'],self.triskelion,self.msi,cap=64)
        (self.repo/'pkg.py').write_text('def transform(x,y): return 123\n')
        git(self.repo,'add','.')
        git(self.repo,'commit','-qm','changed source')
        second=v8.stratified_catalog(self.repo,git(self.repo,'rev-parse','HEAD'),
                                     ['pkg.py'],self.triskelion,self.msi,cap=64)
        self.assertNotEqual(first['original_typed_source_sha256'],second['original_typed_source_sha256'])

    def test_A03_original_legacy_empty_language_never_fabricated(self):
        with self.assertRaises(ValueError):
            v8.stratified_catalog(self.repo,self.sha,['absent.py'],
                                  self.triskelion,self.msi,cap=64)

    def test_A04_original_cap_is_bound_and_no_new_builder_supplied(self):
        for cap in (0,-1,65):
            with self.assertRaises(ValueError):
                v8.stratified_catalog(self.repo,self.sha,['pkg.py'],
                                      self.triskelion,self.msi,cap=cap)
        catalog=v8.stratified_catalog(self.repo,self.sha,['pkg.py'],
                                      self.triskelion,self.msi,cap=12)
        self.assertLessEqual(len(catalog['rows']),12)
        self.assertEqual(catalog['source']['v104_signature_count'],75)

if __name__=='__main__':
    unittest.main()
