"""Contracts for original prospective Pareto choice, not a new experiment."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch


SOURCE_REPO = Path(os.environ.get('UDM_SOURCE_REPOS', '/workspace/repos')) / 'test'


class DevelopmentalChoiceTests(unittest.TestCase):
    def setUp(self):
        name = 'research.unified_consequence_runtime.developmental_choice'
        self.assertIsNotNone(importlib.util.find_spec(name), 'choice adapter missing')
        from research.unified_consequence_runtime import developmental_choice
        self.choice = developmental_choice
        self.candidates = ('retained', 'candidate')
        self.futures = ('first', 'second')
        self.profiles = {
            'retained': {'first': [4, 1], 'second': [3, 0]},
            'candidate': {'first': [2, 0], 'second': [3, 0]},
        }
        self.scope = {'task_source': 'contract-fixture', 'receipt_ids': ['r1', 'r2']}

    def binding(self, candidates=None, futures=None, profiles=None):
        return self.choice.profile_binding(
            self.candidates if candidates is None else candidates,
            self.futures if futures is None else futures,
            self.profiles if profiles is None else profiles,
            scope=self.scope,
        )

    def call(self, *, candidates=None, futures=None, profiles=None, binding=None, source=SOURCE_REPO):
        return self.choice.choose_verified_profiles(
            source,
            self.candidates if candidates is None else candidates,
            self.futures if futures is None else futures,
            self.profiles if profiles is None else profiles,
            evidence_binding=self.binding() if binding is None else binding,
        )

    def test_original_choice_definitions_only_and_exact_source(self):
        native = self.choice.native_choice(SOURCE_REPO)
        self.assertEqual(native['choose'].__code__.co_filename,
                         'git:' + self.choice.SOURCE_PIN['commit'] + ':' + self.choice.SOURCE_PIN['path'])
        self.assertNotIn('TARGET', native['choose'].__globals__)
        self.assertNotIn('consequence', native['choose'].__globals__)
        self.assertNotIn('main', native['choose'].__globals__)
        self.assertEqual(self.choice.SOURCE_PIN['sha256'],
                         'ef46969e2182a5ced64e3c80f5266c03f864d72dcd8133539e6b1a71c42a4b94')

    def test_unique_original_pareto_choice_preserves_full_frontier(self):
        result = self.call()
        self.assertEqual(result['status'], 'AUTHORIZED_REPAIR')
        self.assertEqual(result['selected'], 'candidate')
        self.assertEqual(result['candidates'], list(self.candidates))
        self.assertEqual(result['sources']['prospective_repair_selection'], self.choice.SOURCE_PIN)
        self.assertEqual(result['independent_authority'], 'NOT_ESTABLISHED_BY_THIS_BINDING')
        self.assertFalse(result['grammar_extension_licensed'])
        self.assertEqual(result['expressivity'], 'UNKNOWN')

    def test_complete_binding_hash_includes_source_scope_and_carriers(self):
        binding = self.binding()
        material = {'source': self.choice.SOURCE_PIN, 'scope': self.scope,
                    'candidates': list(self.candidates), 'futures': list(self.futures),
                    'profiles': self.profiles}
        digest = hashlib.sha256(json.dumps(material, sort_keys=True, separators=(',', ':'),
                                          ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()
        self.assertEqual(binding, {'source': self.choice.SOURCE_PIN, 'scope': self.scope,
                                   'profiles_sha256': digest})

    def test_tie_preserves_all_lawful_candidates(self):
        profiles = deepcopy(self.profiles)
        profiles['candidate'] = deepcopy(profiles['retained'])
        result = self.call(profiles=profiles, binding=self.binding(profiles=profiles))
        self.assertEqual(result['status'], 'UNKNOWN_CHOICE')
        self.assertIsNone(result['selected'])
        self.assertEqual(result['candidates'], list(self.candidates))

    def test_incomparable_profiles_preserve_unknown_choice(self):
        profiles = deepcopy(self.profiles)
        profiles['candidate']['second'] = [4, 0]
        result = self.call(profiles=profiles, binding=self.binding(profiles=profiles))
        self.assertEqual(result['status'], 'UNKNOWN_CHOICE')
        self.assertIsNone(result['selected'])

    def test_single_candidate_with_empty_profile_never_wins_vacuously(self):
        result = self.call(candidates=('only',), futures=(), profiles={'only': {}}, binding={})
        self.assertEqual(result['status'], 'UNKNOWN_CHOICE')
        self.assertIsNone(result['selected'])

    def test_empty_or_duplicate_carriers_are_unknown(self):
        for candidates, futures, profiles in [
            ((), self.futures, {}),
            (('same', 'same'), self.futures, {'same': {'first': [0], 'second': [0]}}),
            (self.candidates, ('same', 'same'), self.profiles),
            (('',), self.futures, {'': {'first': [0], 'second': [0]}}),
        ]:
            with self.subTest(candidates=candidates, futures=futures):
                result = self.call(candidates=candidates, futures=futures, profiles=profiles, binding={})
                self.assertEqual(result['status'], 'UNKNOWN_CHOICE')
                self.assertIsNone(result['selected'])

    def test_missing_or_extra_candidate_and_future_keys_are_unknown(self):
        mutations = []
        p = deepcopy(self.profiles); p.pop('retained'); mutations.append(p)
        p = deepcopy(self.profiles); p['extra'] = p['retained']; mutations.append(p)
        p = deepcopy(self.profiles); p['retained'].pop('second'); mutations.append(p)
        p = deepcopy(self.profiles); p['retained']['extra'] = [0, 0]; mutations.append(p)
        for profiles in mutations:
            with self.subTest(profiles=profiles):
                result = self.call(profiles=profiles, binding={})
                self.assertEqual(result['status'], 'UNKNOWN_CHOICE')
                self.assertIsNone(result['selected'])

    def test_truncated_and_empty_vectors_are_unknown(self):
        for vector in ([], [0], [0, 0, 0]):
            profiles = deepcopy(self.profiles); profiles['candidate']['second'] = vector
            with self.subTest(vector=vector):
                result = self.call(profiles=profiles, binding={})
                self.assertEqual(result['status'], 'UNKNOWN_CHOICE')
                self.assertIsNone(result['selected'])

    def test_bool_nan_inf_and_non_numeric_coordinates_are_unknown(self):
        for value in (True, False, float('nan'), float('inf'), -float('inf'), '0', None):
            profiles = deepcopy(self.profiles); profiles['candidate']['second'] = [value, 0]
            with self.subTest(value=value):
                result = self.call(profiles=profiles, binding={})
                self.assertEqual(result['status'], 'UNKNOWN_CHOICE')
                self.assertIsNone(result['selected'])

    def test_finite_negative_float_coordinates_are_allowed(self):
        profiles = deepcopy(self.profiles); profiles['candidate']['first'] = [-0.5, 0.0]
        result = self.call(profiles=profiles, binding=self.binding(profiles=profiles))
        self.assertEqual(result['selected'], 'candidate')

    def test_missing_binding_is_unknown_evidence(self):
        for binding in ({}, None, {'profiles_sha256': '0' * 64}):
            result = self.choice.choose_verified_profiles(
                SOURCE_REPO, self.candidates, self.futures, self.profiles, evidence_binding=binding)
            self.assertEqual(result['status'], 'UNKNOWN_EVIDENCE')
            self.assertIsNone(result['selected'])

    def test_altered_profiles_scope_or_source_cannot_replay_binding(self):
        profiles = deepcopy(self.profiles); profiles['candidate']['first'] = [1, 0]
        result = self.call(profiles=profiles, binding=self.binding())
        self.assertEqual(result['status'], 'UNKNOWN_EVIDENCE')
        for key in ('scope', 'source'):
            binding = self.binding(); binding[key] = {'wrong': 'source-or-scope'}
            result = self.call(binding=binding)
            self.assertEqual(result['status'], 'UNKNOWN_EVIDENCE')
            self.assertIsNone(result['selected'])

    def test_caller_supplied_winner_does_not_authorize_choice(self):
        binding = self.binding(); binding['selected'] = 'retained'
        result = self.call(binding=binding)
        self.assertEqual(result['status'], 'UNKNOWN_EVIDENCE')
        self.assertIsNone(result['selected'])

    def test_missing_source_is_unknown_even_after_prior_success(self):
        self.assertEqual(self.call()['status'], 'AUTHORIZED_REPAIR')
        result = self.call(source=Path('/this-choice-source-does-not-exist'))
        self.assertEqual(result['status'], 'UNKNOWN_SOURCE')
        self.assertIsNone(result['selected'])

    def test_altered_executable_is_rejected_before_ast_execution(self):
        with patch.object(self.choice, '_source_bytes', return_value=b'raise RuntimeError("must not run")'):
            result = self.call()
        self.assertEqual(result['status'], 'UNKNOWN_SOURCE')
        self.assertIsNone(result['selected'])


if __name__ == '__main__':
    unittest.main()
