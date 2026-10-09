import sys,unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_shopping_wishlist_blind import authorize_intent,verify_start_url


class WishlistAdmission(unittest.TestCase):
    def test_intent(self):
        authorize_intent("Add the product on the current page to my wishlist")
        with self.assertRaises(ValueError):
            authorize_intent("Buy the product on this page")

    def test_start_url(self):
        self.assertEqual(
            verify_start_url("__SHOPPING__/example-item.html"),
            "http://localhost:7770/example-item.html",
        )
        for url in ("__GITLAB__/x.html","__SHOPPING__/","https://external.invalid/x.html"):
            with self.assertRaises(ValueError):
                verify_start_url(url)

    def test_no_task_dispatch(self):
        src=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_shopping_wishlist_blind.py").read_text()
        for forbidden in ("task_id","intent_template_id","instantiation_dict","evaluate_task","expected_answer"):
            self.assertNotIn(forbidden,src)


if __name__=="__main__":
    unittest.main()
