import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_gitlab_milestone_blind import parse_intent

class BlindMilestone(unittest.TestCase):
    def test_relative_and_absolute_dates(self):
        cases=[
            ("Create a milestone in the current repo with title \"product launch\" for the upcoming event of product launch starting on January 16, 2023 and ending on January 30, 2023","2023-01-16","2023-01-30"),
            ("Create a milestone in the current repo with title \"code review\" for the upcoming practice of collective code review starting on January 16, 2023 and ending in 20 days (inclusive)","2023-01-16","2023-02-04"),
            ("Create a milestone in the current repo with title \"sensitive information\" for the upcoming task of cleaning sensitive information starting on February 16, 2023 and ending in 20 days (inclusive)","2023-02-16","2023-03-07"),
        ]
        for intent,start,end in cases:
            spec=parse_intent(intent,"__GITLAB__/primer/design")
            self.assertEqual((spec["start_date"],spec["due_date"]),(start,end))

    def test_unknown_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_intent("Delete all milestones","__GITLAB__/primer/design")
        with self.assertRaises(ValueError):
            parse_intent(
                'Create a milestone in the current repo with title "x" for the upcoming task starting on January 16, 2023 and ending in 20 days (inclusive)',
                "__REDDIT__"
            )

    def test_no_evaluator_routing(self):
        s=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_gitlab_milestone_blind.py").read_text()
        for q in ("task_id","intent_template_id","instantiation_dict","expected_answer","evaluate_task"):
            self.assertNotIn(q,s)
if __name__=="__main__":
    unittest.main()
