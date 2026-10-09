"""Behavioral admission controls for independently green capability families."""
import sys
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from webarena_blind_proven_additions import select_route, run


class VerifiedPromotionRouting(unittest.TestCase):
    def test_catalog_sort_from_user_intent_only(self):
        text = 'Pull up the page with all "iphone 12 phone case" listings sorted by name alphabetically.'
        self.assertEqual(select_route(text, '__SHOPPING__'), 'shopping_sort')
        self.assertIsNone(select_route(text, '__GITLAB__'))

    def test_cross_site_review_from_user_intent_only(self):
        text = ('Create a post in the game related discussion forum about HORI 3D Surround Gaming Neckset '
                'to report customer reviews with 2 stars and less rating from the OneStopShop '
                'with the post title "real user feedback on HORI 3D Surround Gaming Neckset". '
                'Format the post body as a bullet point list in the same order they appear '
                '(md format: - "<review title>").')
        self.assertEqual(select_route(text, '__SHOPPING__'), 'shopping_reddit_review')
        self.assertIsNone(select_route(text, '__REDDIT__'))

    def test_gitlab_fork_family_selects_by_intent_not_metadata(self):
        for intent in (
            'Fork MetaSeq.',
            'Fork all repos from Akilesh Kannan.',
            'Fork all repos from facebook.',
        ):
            with self.subTest(intent=intent):
                self.assertEqual(select_route(intent, '__GITLAB__'), 'gitlab_fork')
                self.assertIsNone(select_route(intent, '__SHOPPING__'))
        for malformed in ('Fork ../private.', 'Fork everything in company'):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                select_route(malformed, '__GITLAB__')

    def test_gitlab_reviewer_navigation(self):
        query = 'Go to the merge requests requiring my review'
        self.assertEqual(select_route(query, '__GITLAB__'), 'navigation_transfer')
        self.assertIsNone(select_route(query, '__SHOPPING_ADMIN__'))

    def test_admin_tax_navigation(self):
        query = 'Show the tax report for for this year (today is March 15, 2023).'
        self.assertEqual(select_route(query, '__SHOPPING_ADMIN__'), 'navigation_transfer')
        self.assertIsNone(select_route(query, '__GITLAB__'))

    def test_unrelated_messages_delegate(self):
        for intent in ('Delete all stores', 'Buy all products', '',
                       'Get the total number of reviews that our store received so far that mention term "excellent"'):
            self.assertIsNone(select_route(intent, '__SHOPPING__'))

    def test_agent_source_has_no_evaluator_lookup(self):
        source = (ROOT / 'scripts' / 'webarena_blind_proven_additions.py').read_text()
        for forbidden in ('task_id', 'intent_template_id', 'instantiation_dict',
                          'evaluate_task', 'expected_answer', 'hard.json'):
            self.assertNotIn(forbidden, source)


class PromotionDispatch(unittest.IsolatedAsyncioTestCase):
    async def test_verified_and_fallback_execution_receive_unchanged_inputs(self):
        cases = [
            ('__SHOPPING__',
             'Pull up the page with all "phone cases" listings sorted by price.',
             'webarena_shopping_sort_blind'),
            ('__SHOPPING__',
             'Create a post in the game related discussion forum about a Game Console '
             'to report customer reviews with 2 stars rating from the OneStopShop',
             'webarena_shopping_reddit_review_compound'),
            ('__GITLAB__', 'Go to the merge requests requiring my review',
             'webarena_blind_navigation_transfer'),
            ('__GITLAB__', 'Fork MetaSeq.',
             'webarena_gitlab_fork_blind'),
            ('__SHOPPING_ADMIN__', 'Show the tax report for this year (today is March 15, 2023).',
             'webarena_blind_navigation_transfer'),
            ('__REDDIT__', 'Get the newest post in books',
             'webarena_blind_retrieval_bridge'),
        ]
        for site, intent, module_name in cases:
            with self.subTest(site=site, module=module_name):
                stub = ModuleType(module_name)
                stub.run = AsyncMock(return_value={'result': 'observed'})
                if module_name == 'webarena_gitlab_fork_blind':
                    from webarena_gitlab_fork_blind import parse_fork_intent
                    stub.parse_fork_intent = parse_fork_intent
                out = Path('/tmp/opaque-observation')
                with patch.dict(sys.modules, {module_name: stub}):
                    result = await run(intent, site, out)
                stub.run.assert_awaited_once_with(intent, site, out)
                self.assertEqual(result, {'result': 'observed'})

    async def test_ambiguous_fork_is_not_replayed_as_fallback(self):
        chosen = ModuleType('webarena_gitlab_fork_blind')
        from webarena_gitlab_fork_blind import parse_fork_intent
        chosen.parse_fork_intent = parse_fork_intent
        chosen.run = AsyncMock(side_effect=RuntimeError('ambiguous fork result'))
        fallback = ModuleType('webarena_blind_retrieval_bridge')
        fallback.run = AsyncMock()
        with patch.dict(sys.modules, {'webarena_gitlab_fork_blind': chosen,
                                      'webarena_blind_retrieval_bridge': fallback}):
            with self.assertRaisesRegex(RuntimeError, 'ambiguous fork result'):
                await run('Fork MetaSeq.', '__GITLAB__', Path('/tmp/test'))
        chosen.run.assert_awaited_once()
        fallback.run.assert_not_awaited()

    async def test_ambiguous_write_is_not_replayed_as_fallback(self):
        chosen = ModuleType('webarena_shopping_reddit_review_compound')
        chosen.run = AsyncMock(side_effect=RuntimeError('ambiguous write result'))
        fallback = ModuleType('webarena_blind_retrieval_bridge')
        fallback.run = AsyncMock()
        query = ('Create a post in the game related discussion forum about a Test '
                 'to report customer reviews with 2 stars rating from the OneStopShop')
        with patch.dict(sys.modules, {'webarena_shopping_reddit_review_compound': chosen,
                                      'webarena_blind_retrieval_bridge': fallback}):
            with self.assertRaisesRegex(RuntimeError, 'ambiguous write result'):
                await run(query, '__SHOPPING__', Path('/tmp/test'))
        chosen.run.assert_awaited_once()
        fallback.run.assert_not_awaited()


if __name__ == '__main__':
    unittest.main()
