"""Fail-closed Playwright navigation-timeout postcondition tests."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_reddit_submit_v3 import postcondition


class PostconditionTests(unittest.TestCase):
    def test_actual_post_verification(self):
        self.assertTrue(postcondition(
            "http://localhost:9999/f/iphone/2/used-iphone-recommendations",
            "iphone","used iphone recommendations?",
            "New post: used iphone recommendations? by MarvelsGrantMan136"
        ))

    def test_wrong_forum_or_title_is_rejected(self):
        for url,forum,title,body in (
            ("http://localhost:9999/submit/iphone","iphone","used iphone recommendations?","used iphone recommendations?"),
            ("http://localhost:9999/f/books/2/used-iphone-recommendations","iphone","used iphone recommendations?","used iphone recommendations?"),
            ("http://localhost:9999/f/iphone/2/other","iphone","used iphone recommendations?","Completely unrelated title"),
            ("http://localhost:9999/f/iphone/not-an-id/used-iphone-recommendations","iphone","used iphone recommendations?","used iphone recommendations?"),
        ):
            self.assertFalse(postcondition(url,forum,title,body))

    def test_no_task_or_evaluator_access(self):
        src=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_reddit_submit_v3.py").read_text()
        start=src.index("def postcondition(")
        end=src.index("async def main():")
        portion=src[start:end]
        self.assertNotIn("task_id",portion)
        self.assertNotIn("intent_template_id",portion)
        self.assertNotIn("expected_answer",portion)


if __name__=="__main__":
    unittest.main()
