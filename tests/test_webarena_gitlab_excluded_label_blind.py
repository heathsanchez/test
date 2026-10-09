import sys,unittest
from pathlib import Path
from urllib.parse import urlparse,parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_gitlab_excluded_label_blind import parse_intent,filtered_target

class NegativeLabelNavigation(unittest.TestCase):
    def test_generic_negative_label_operator(self):
        a=parse_intent(
            "Navigate to the page showing the list of open issues in the "
            "umano/AndroidSlidingUpPanel repository that have labels related "
            "to all except BUG"
        )
        self.assertEqual(a,{"repo":"umano/AndroidSlidingUpPanel","excluded_label":"BUG"})
        url=filtered_target(a)
        query=parse_qs(urlparse(url).query)
        self.assertEqual(query["state"],["opened"])
        self.assertEqual(query["not[label_name][]"],["BUG"])

    def test_bad_or_unsafe_names_fail_closed(self):
        for text in (
            "Navigate to arbitrary URL",
            "Navigate to the page showing the list of open issues in "
            "../secrets repository that have labels related to all except BUG",
        ):
            with self.assertRaises(ValueError):
                parse_intent(text)

    def test_no_benchmark_identifiers(self):
        src=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_gitlab_excluded_label_blind.py").read_text()
        for token in ("task_id","intent_template_id","instantiation_dict","expected_answer","evaluate_task"):
            self.assertNotIn(token,src)

if __name__=="__main__":
    unittest.main()
