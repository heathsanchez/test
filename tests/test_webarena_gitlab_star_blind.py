"""Network-mutation preconditions for intent-only GitLab star ranking."""
from pathlib import Path
import sys, unittest
from unittest.mock import AsyncMock, patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
MODULE=ROOT/'scripts'/'webarena_gitlab_star_blind.py'

class StarIntent(unittest.TestCase):
    def test_agent_module_exists(self):
        self.assertTrue(MODULE.is_file(),'missing GitLab star agent')

    def test_count_is_from_user_language(self):
        from webarena_gitlab_star_blind import parse_intent
        for phrase,n in [('three',3),('four',4),('five',5)]:
            for adjective in ('stared','starred'):
                self.assertEqual(parse_intent(f'Star the top {phrase} most {adjective} repos in Gitlab'),n)

    def test_selection_preserves_provider_ranked_evidence(self):
        from webarena_gitlab_star_blind import choose_projects
        records=[{'id':8,'star_count':37,'path_with_namespace':'a/first'},
                 {'id':17,'star_count':30,'path_with_namespace':'b/second'},
                 {'id':22,'star_count':30,'path_with_namespace':'c/third'},
                 {'id':9,'star_count':27,'path_with_namespace':'d/fourth'}]
        self.assertEqual([x['id'] for x in choose_projects(records,3)],[8,17,22])
        with self.assertRaises(ValueError):choose_projects(records[::-1],3)
        with self.assertRaises(ValueError):choose_projects(records,5)

    def test_fail_closed_on_unsupported_or_cross_site(self):
        from webarena_gitlab_star_blind import parse_intent,validate_start
        for text in ('Star all repositories','Unstar every project','Star the top 500 most starred repos in Gitlab'):
            with self.assertRaises(ValueError):parse_intent(text)
        with self.assertRaises(ValueError):validate_start('__REDDIT__')

    def test_no_evaluator_or_task_identity(self):
        source=MODULE.read_text()
        for forbidden in ('task_id','intent_template_id','instantiation_dict','expected_answer','evaluate_task'):
            self.assertNotIn(forbidden,source)

class StarObservation(unittest.IsolatedAsyncioTestCase):
    async def test_single_post_per_project_and_independent_readback(self):
        from webarena_gitlab_star_blind import perform
        api_rows=[{'id':8,'star_count':37,'path_with_namespace':'a/first'},
                  {'id':17,'star_count':30,'path_with_namespace':'b/second'}]
        calls=[]
        async def observed(page,method,path):
            calls.append((method,path))
            if method=='GET' and 'starred=true' not in path and '&page=1' in path:return api_rows
            if method=='POST' and path.endswith('/star'):return {'status':201}
            if method=='GET' and 'starred=true' in path:return api_rows
            raise AssertionError((method,path))
        with patch('webarena_gitlab_star_blind.api_request',side_effect=observed):
            evidence=await perform(None,2)
        self.assertEqual(len([x for x in calls if x[0]=='POST']),2)
        self.assertEqual(evidence['verified_project_ids'],[8,17])

if __name__=='__main__':unittest.main()



class LocalStarRankingTests(unittest.IsolatedAsyncioTestCase):
    async def test_reads_every_page_before_ranking_and_writing(self):
        from unittest.mock import patch
        from webarena_gitlab_star_blind import perform
        # The most starred projects can appear outside the first API page.
        early=[{'id':i,'star_count':2,'path_with_namespace':f'group/p{i}'}
               for i in range(1,101)]
        late=[{'id':101,'star_count':900,'path_with_namespace':'group/best'},
              {'id':102,'star_count':700,'path_with_namespace':'group/second'},
              {'id':103,'star_count':600,'path_with_namespace':'group/third'}]
        observed=[]
        async def request(page,method,path):
            observed.append((method,path))
            if 'order_by=star_count' in path:
                raise RuntimeError('fixture API: order_by does not have a valid value')
            if method=='GET' and 'starred=true' in path:
                return late
            if method=='GET' and '&page=1' in path:
                return early
            if method=='GET' and '&page=2' in path:
                return late
            if method=='POST' and path.endswith('/star'):
                return {'status':201}
            raise AssertionError((method,path))
        with patch('webarena_gitlab_star_blind.api_request',side_effect=request):
            evidence=await perform(None,3)
        self.assertEqual(evidence['verified_project_ids'],[101,102,103])
        self.assertEqual(evidence['observed_project_count'],103)
        self.assertEqual(evidence['observed_pages'],2)
        self.assertEqual(len([call for call in observed if call[0]=='POST']),3)
        self.assertLess(observed.index(next(c for c in observed if c[0]=='GET' and '&page=2' in c[1])),
                        observed.index(next(c for c in observed if c[0]=='POST')))
