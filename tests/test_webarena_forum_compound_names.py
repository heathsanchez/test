"""Offline replay of observed forum candidates, plus unrelated control inputs."""
from __future__ import annotations

import importlib.util
import json
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    '_forum_resolver', ROOT / 'scripts' / 'webarena_reddit_forum_resolver.py'
)
RESOLVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESOLVER)
FIXTURE = json.loads((Path(__file__).parent / 'fixtures' / 'webarena_observed_forums.json').read_text())


def rank(query, rows=None):
    rows = FIXTURE['candidates'] if rows is None else rows
    return sorted(rows, key=lambda row: (
        -RESOLVER.score(query, row['label'], row['slug'], row['context']), row['slug']
    ))


class CompoundForumTests(unittest.TestCase):
    def test_captured_deep_learning_regression(self):
        query = 'the effectiveness of deep learning'
        self.assertEqual(rank(query)[0]['slug'], 'deeplearning')

    def test_captured_durability_gain_is_preserved(self):
        query = ('Must have product at last for ever recommendations '
                 'I need recommendations for Must have product at last for ever '
                 'within a budget of $30 please')
        self.assertEqual(rank(query)[0]['slug'], 'BuyItForLife')

    def test_other_captured_semantic_queries_remain_stable(self):
        controls = {
            'DIY toolkit recommendations I need recommendations for DIY toolkit within a budget of $100 please': 'DIY',
            'relations relationship advice': 'relationship_advice',
            'games': 'gaming',
            'safe and budget apartment to live in nyc': 'nyc',
        }
        for query, slug in controls.items():
            with self.subTest(query=query):
                self.assertEqual(rank(query)[0]['slug'], slug)

    def test_rank_is_independent_of_candidate_order(self):
        rows = list(FIXTURE['candidates'])
        for seed in range(10):
            random.Random(seed).shuffle(rows)
            self.assertEqual(rank('the effectiveness of deep learning', rows)[0]['slug'], 'deeplearning')

    def test_generalizes_to_an_unrelated_compound(self):
        rows = [
            {'slug': 'ArtsAndCrafts', 'label': 'ArtsAndCrafts', 'context': ''},
            {'slug': 'modernart', 'label': 'modernart', 'context': ''},
        ]
        self.assertEqual(rank('modern art recommendations', rows)[0]['slug'], 'modernart')

    def test_case_variants_have_the_same_literal_evidence(self):
        helper = getattr(RESOLVER, 'compound_name_match', lambda *_: 0)
        self.assertGreater(helper('deep learning', 'deeplearning'), 0)
        self.assertEqual(helper('deep learning', 'deeplearning'), helper('deep learning', 'DeepLearning'))

    def test_subword_fragments_are_not_literal_name_evidence(self):
        helper = getattr(RESOLVER, 'compound_name_match', lambda *_: 0)
        self.assertEqual(helper('artificial intelligence', 'Art'), 0)
        self.assertEqual(helper('party ideas', 'Art'), 0)

    def test_noncontiguous_words_are_not_literal_name_evidence(self):
        helper = getattr(RESOLVER, 'compound_name_match', lambda *_: 0)
        self.assertEqual(helper('deep discussion about learning', 'deeplearning'), 0)

    def test_trivial_filler_does_not_become_a_forum_match(self):
        helper = getattr(RESOLVER, 'compound_name_match', lambda *_: 0)
        self.assertEqual(helper('I am a beginner in woodworking', 'IAmA'), 0)

    def test_numeral_expansion_is_preserved(self):
        self.assertIn('explainlikeimfive', RESOLVER.candidate_forum_slugs('explain like im 5'))
        self.assertNotIn('eli5', RESOLVER.candidate_forum_slugs('explain like im 5'))

    def test_runtime_does_not_read_fixture_or_benchmark_answers(self):
        source = (ROOT / 'scripts' / 'webarena_reddit_forum_resolver.py').read_text()
        for forbidden in ('webarena_observed_forums', 'task_id', 'intent_template_id', 'instantiation_dict', 'expected_answer'):
            self.assertNotIn(forbidden, source)
        # These literals identify observed examples, not a permitted dispatch table.
        for forbidden in ('"MachineLearning"', '"deeplearning"'):
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
