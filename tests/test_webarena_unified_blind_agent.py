"""Pure-boundary controls for the unified task-ID-blind agent."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from webarena_unified_blind_agent import (
    gitlab_intent,site_from_start,actual_start,
)


class UnifiedBlindRouterTests(unittest.TestCase):
    def test_site_routes_only_from_initial_url(self):
        self.assertEqual(site_from_start("__REDDIT__"),"reddit")
        self.assertEqual(site_from_start("__GITLAB__"),"gitlab")
        self.assertEqual(site_from_start("__GITLAB__/a11yproject/a11yproject.com"),"gitlab")
        self.assertEqual(site_from_start("http://localhost:8023/a11yproject/a11yproject.com"),"gitlab")
        self.assertEqual(site_from_start("http://localhost:9999/f/books/59421"),"reddit")
        with self.assertRaises(ValueError):
            site_from_start("__SHOPPING__")
        with self.assertRaises(ValueError):
            site_from_start("https://github.com")

    def test_gitlab_rss(self):
        self.assertEqual(gitlab_intent("Get me my RSS feed token"),("rss",{}))

    def test_gitlab_personal_stars(self):
        for desc in ("the least stars","less than 5 stars","no stars"):
            action,args=gitlab_intent(
                f"Get the project ID(s) of my personal project(s) that received {desc}"
            )
            self.assertEqual(action,"personal_project_stars")
            self.assertEqual(args["description"],desc)

    def test_gitlab_commit_periods(self):
        examples=[
            ("How many commits did Kilian make during 2023 in the current repository?","Kilian","during 2023"),
            ("How many commits did Eric Bailey make between start of Feb 2023 and end of May 2023 in the current repository?","Eric Bailey","between start of Feb 2023 and end of May 2023"),
            ("How many commits did Nic Chan make on April 7th 2022 in the current repository?","Nic Chan","on April 7th 2022"),
        ]
        for text,author,period in examples:
            route,args=gitlab_intent(text)
            self.assertEqual(route,"commit_count")
            self.assertEqual(args,{"author":author,"period":period})

    def test_out_of_grammar_fails_closed(self):
        with self.assertRaises(ValueError):
            gitlab_intent("Delete every project in GitLab")
        with self.assertRaises(ValueError):
            gitlab_intent("How many commits did X make some time in the current repository?")

    def test_start_translation_does_not_inspect_task_metadata(self):
        self.assertEqual(
            actual_start("__GITLAB__/a11yproject/a11yproject.com"),
            "http://localhost:8023/a11yproject/a11yproject.com",
        )

    def test_agent_source_has_no_benchmark_lookup(self):
        src=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_unified_blind_agent.py").read_text()
        for forbidden in ("task_id","intent_template_id","instantiation_dict","expected_answer","evaluate_task"):
            self.assertNotIn(forbidden,src)


if __name__=="__main__":
    unittest.main()
