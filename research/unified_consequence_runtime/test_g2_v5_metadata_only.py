"""Adversarial, no-network contracts for the frozen V5 metadata-only intake.

They establish boundary correctness, not prospective method learning.
"""
import json
from pathlib import Path
import unittest

from . import g2_v5_metadata_only as m


class FakeAPI:
    def __init__(self,records=None):
        self.records=records or {}
        self.paths_seen=[]
        self.calls=0
    def matching_prs(self,repo,max_results):
        self.calls+=1
        return self.records.get(repo,[])
    def paths(self,repo,number,max_pages):
        self.paths_seen.append((repo,number))
        return [
            {'path':'src/pkg/logic.py','status':'modified'},
            {'path':'tests/test_logic.py','status':'modified'}
        ]
    def get(self,path):
        self.calls+=1
        if '/commits/' in path:
            return {'parents':[{'sha':'b'*40}]}
        return {'merged_at':'2026-05-01T11:00:00Z',
                'merge_commit_sha':'c'*40,'head':{'sha':'d'*40}}


class V5MetadataContracts(unittest.TestCase):
    def test_01_frozen_source_blind_universe_disjoint_from_exclusions(self):
        config,digest=m.read_spec()
        self.assertEqual(len(config['source_blind_repo_order']),12)
        self.assertEqual(len(digest),64)
        self.assertFalse(set(x.lower() for x in config['source_blind_repo_order']) &
                         set(x.lower() for x in config['historical_exclusions']))

    def test_02_original_v4_universe_is_not_clean_and_not_rewritten(self):
        p=m.ROOT/'research/unified_consequence_runtime/G2_TRANSFER_INTERFACE_V4_PREQUERY_20261018.json'
        old=json.loads(p.read_text())
        known=set(x.lower() for x in m.read_spec()[0]['historical_exclusions'])
        collision=set(x.lower() for x in old['new_repository_universe']) & known
        self.assertGreaterEqual(len(collision),3)
        self.assertEqual(old['status'],'NOT_RUN')

    def test_03_valid_pair(self):
        self.assertEqual(m.eligible_paths([
            {'path':'src/pkg/driver.py','status':'modified'},
            {'path':'tests/test_driver.py','status':'added'}])[0],'ELIGIBLE')

    def test_04_changed_build_and_dependencies_refused(self):
        for path in ('pyproject.toml','setup.py','requirements/test.txt',
                     'tox.ini','uv.lock','.github/workflows/test.yml',
                     'ci/tests.sh','src/pak/noxfile.py'):
            with self.subTest(path=path):
                files=[{'path':'src/pkg/logic.py','status':'modified'},
                       {'path':'tests/test_logic.py','status':'modified'},
                       {'path':path,'status':'modified'}]
                self.assertNotEqual(m.eligible_paths(files)[0],'ELIGIBLE')

    def test_05_multiple_python_edits_refused(self):
        for path in ('src/pkg/other.py','tests/test_other.py',
                     'docs/conf.py','examples/demo.py'):
            files=[{'path':'src/pkg/logic.py','status':'modified'},
                   {'path':'tests/test_logic.py','status':'modified'},
                   {'path':path,'status':'modified'}]
            with self.subTest(path=path):
                self.assertNotEqual(m.eligible_paths(files)[0],'ELIGIBLE')

    def test_06_removed_or_renamed_python_refused(self):
        for status in ('removed','renamed','copied'):
            with self.subTest(status=status):
                files=[{'path':'src/pkg/logic.py','status':status},
                       {'path':'tests/test_logic.py','status':'modified'}]
                self.assertEqual(m.eligible_paths(files)[0],
                                 'UNSUPPORTED_FILE_CHANGE_KIND')

    def test_07_parent_traversal_and_noncanonical_path_refused(self):
        for path in ('src/../evil.py','src/a/../driver.py',
                     'tests/../test_logic.py','tests/a/../test_logic.py',
                     'src/pkg//logic.py'):
            with self.subTest(path=path):
                files=[{'path':path,'status':'modified'},
                       {'path':'tests/test_logic.py','status':'modified'}]
                self.assertNotEqual(m.eligible_paths(files)[0],'ELIGIBLE')

    def test_08_first_qualifying_pr_and_repo_order(self):
        config=m.read_spec()[0].copy()
        config['source_blind_repo_order']=['x/one','y/two','z/three','w/four','v/five']
        records={r:[{'number':i+5,'created_at':'2026-03-01T00:00:00Z'}]
                 for i,r in enumerate(config['source_blind_repo_order'])}
        api=FakeAPI(records)
        selected,reasons=m.shortlist(config,api)
        self.assertEqual([x['repo'] for x in selected],
                         ['x/one','y/two','z/three','w/four'])
        self.assertFalse(any(x[0]=='v/five' for x in api.paths_seen))
        self.assertEqual(len(selected),4)
        self.assertTrue(all(x['source']=='GITHUB_METADATA_ONLY_NO_PATCH_EXPOSURE'
                            for x in selected))

    def test_09_shortfall_no_automatic_replacement(self):
        config=m.read_spec()[0].copy()
        config['source_blind_repo_order']=['x/one','y/two']
        api=FakeAPI({'x/one':[{'number':7,'created_at':'2026-01-01'}]})
        selected,_=m.shortlist(config,api)
        self.assertEqual(len(selected),1)
        self.assertEqual(selected[0]['number'],7)

    def test_10_metadata_projection_contains_no_source_or_patch(self):
        config=m.read_spec()[0].copy()
        config['source_blind_repo_order']=['x/one']
        selected,_=m.shortlist(config,FakeAPI({'x/one':[{'number':7,'created_at':'2026-02-03'}]}))
        encoded=json.dumps(selected)
        self.assertNotIn('patch',encoded.lower())
        self.assertNotIn('diff',encoded.lower())
        self.assertNotIn('return True',encoded)
        self.assertFalse(any('author_test_body' in x for x in selected))


if __name__=='__main__':
    unittest.main()
