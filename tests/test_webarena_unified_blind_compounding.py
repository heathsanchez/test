import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_unified_blind_compounding import select_new_primitive


class CompoundedBlindRouting(unittest.TestCase):
    def test_wishlist_action_is_site_and_intent_specific(self):
        statement="Add the product on the current page to my wishlist"
        self.assertEqual(
            select_new_primitive(statement,"__SHOPPING__/example-product.html"),
            "shopping_wishlist_add",
        )
        self.assertIsNone(select_new_primitive(statement,"__GITLAB__"))
        self.assertIsNone(select_new_primitive(statement,"__REDDIT__"))

    def test_other_intents_delegate_unchanged(self):
        self.assertIsNone(select_new_primitive(
            "Get all review titles with 2 stars or below for the product on the current page.",
            "__SHOPPING__/p.html",
        ))
        self.assertIsNone(select_new_primitive(
            "Get the URL to clone Super_Awesome_Robot with SSH. Return the URL only, without any additional details.",
            "__GITLAB__",
        ))

    def test_no_benchmark_dispatch(self):
        src=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_unified_blind_compounding.py").read_text()
        for marker in ("task_id","intent_template_id","instantiation_dict","evaluate_task","expected_answer"):
            self.assertNotIn(marker,src)


if __name__=="__main__":
    unittest.main()
