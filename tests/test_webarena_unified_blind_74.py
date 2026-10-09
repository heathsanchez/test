import sys,unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_unified_blind_74 import new_capability


class ComposedBlindRouting(unittest.TestCase):
    def test_read_families_are_routeable(self):
        examples=[
            (
                'Among the top 10 hottest posts in the "Books" forum, get the post titles from those that recommend exactly one book.',
                "top_singular_books",
            ),
            (
                'In the DIY forum, get the username and post title of the most recent post, and count the number of comments on that post that are not from the author and have more downvotes than upvotes. Return a list of objects with keys "username", "post_title", and "count".',
                "recent_negative_comments",
            ),
        ]
        for intent,kind in examples:
            self.assertEqual(new_capability(intent,"__REDDIT__"),kind)

    def test_verified_shopping_search_sort_is_reused(self):
        self.assertEqual(
            new_capability(
                'Pull up the page with all "mouth night guard" listings sorted by descending price.',
                "__SHOPPING__",
            ),
            "shopping_sort",
        )
        self.assertEqual(
            new_capability(
                'Pull up the page with all "iphone 12 phone case" listings sorted by name alphabetically.',
                "__SHOPPING__",
            ),
            "shopping_sort",
        )
        self.assertIsNone(new_capability(
            'Pull up the page with all "mouth night guard" listings sorted by descending price.',
            "__REDDIT__",
        ))

    def test_mutations_and_other_sites_delegate(self):
        self.assertIsNone(new_capability(
            'Post in books forum with title "A test post"',"__REDDIT__"
        ))
        self.assertIsNone(new_capability(
            "Get me my RSS feed token","__GITLAB__"
        ))
        self.assertIsNone(new_capability(
            "Get all review titles with 2 stars or below for the product on the current page.",
            "__SHOPPING__/p.html",
        ))

    def test_no_benchmark_metadata(self):
        source=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_unified_blind_74.py").read_text()
        for marker in ("task_id","intent_template_id","instantiation_dict","evaluate_task","expected_answer"):
            self.assertNotIn(marker,source)


if __name__=="__main__":
    unittest.main()
