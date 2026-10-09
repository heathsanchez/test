"""Candidate identity separator: no benchmark metadata and no unsafe write."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_reddit_repost_image import candidate_evidence

class SourceIdentity(unittest.TestCase):
    def test_duplicate_search_hits_are_one_candidate(self):
        rows=[{"title":"Bald Eagle image","href":"http://localhost/one.jpg","forum_verified":True}]
        selected,candidates=candidate_evidence("Bald Eagle",rows)
        self.assertEqual(len(candidates),1)
        self.assertEqual(selected["href"],rows[0]["href"])

    def test_tied_images_do_not_authorize_a_post(self):
        rows=[{"title":"Firework photo","href":"http://localhost/one.jpg","forum_verified":True},
              {"title":"Firework photo","href":"http://localhost/two.jpg","forum_verified":True}]
        with self.assertRaisesRegex(RuntimeError,"ambiguous"):
            candidate_evidence("Firework",rows)

    def test_distinct_observed_match_is_admitted(self):
        rows=[{"title":"Firework","href":"http://localhost/one.jpg","forum_verified":True},
              {"title":"An unrelated landscape","href":"http://localhost/two.jpg","forum_verified":True}]
        chosen,_=candidate_evidence("Firework",rows)
        self.assertEqual(chosen["href"],rows[0]["href"])
