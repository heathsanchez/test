"""Source-bound review→forum intent compiler and protected evidence filters."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_shopping_reddit_review_compound import parse_intent,rating_filter,list_body

class ReviewForumComposition(unittest.TestCase):
    def test_threshold_and_exact_star_intents(self):
        examples=[
            ("Sony Computer Entertainment VR","2 stars and less rating","at_most",2),
            ("Nintendo Switch Fortnite Wildcat Console EU","3 stars and less rating","at_most",3),
            ("Racing Wheel Overdrive for Xbox X","1 star rating","exact",1),
            ("Doc and Pies Arcade Factory Cocktail Arcade Machine","3 stars and less rating","at_most",3),
            ("HORI 3D Surround Gaming Neckset","2 stars and less rating","at_most",2),
        ]
        for product,rating,predicate,n in examples:
            intent=(
                f'Create a post in the game related discussion forum about {product} '
                f'to report customer reviews with {rating} from the OneStopShop '
                f'with the post title "real user feedback on {product}". '
                'Format the post body as a bullet point list in the same order '
                'they appear (md format: - "<review title>").'
            )
            request=parse_intent(intent)
            self.assertEqual(request["product"],product)
            self.assertEqual(request["forum_description"],"game")
            self.assertEqual(request["predicate"],predicate)
            self.assertEqual(request["stars"],n)
            self.assertEqual(request["title"],f"real user feedback on {product}")

    def test_preserves_visible_review_order(self):
        observed=[
            {"title":"a poor headset","stars":1},
            {"title":"five stars","stars":5},
            {"title":"disappointing audio","stars":2},
            {"title":"bargain","stars":3},
        ]
        chosen=rating_filter(observed,2,"at_most")
        self.assertEqual([r["title"] for r in chosen],["a poor headset","disappointing audio"])
        self.assertEqual(list_body(chosen),'- "a poor headset"\n- "disappointing audio"')
        self.assertEqual([r["title"] for r in rating_filter(observed,1,"exact")],["a poor headset"])

    def test_independent_duplicate_review_titles_preserve_multiplicity(self):
        observed=[
            {"title":"Repeated complaint","stars":2},
            {"title":"five stars","stars":5},
            {"title":"Repeated complaint","stars":2},
        ]
        chosen=rating_filter(observed,2,"at_most")
        self.assertEqual([row["title"] for row in chosen],
                         ["Repeated complaint","Repeated complaint"])
        self.assertEqual(list_body(chosen),
                         '- "Repeated complaint"\n- "Repeated complaint"')

    def test_no_unsupported_empty_post(self):
        with self.assertRaises(ValueError):
            list_body([])

    def test_fails_closed_for_other_actions(self):
        for text in (
            "Delete all my Shopping orders and then create a post",
            "Post a product review without checking it",
        ):
            with self.assertRaises(ValueError):parse_intent(text)

    def test_no_benchmark_or_evaluator_metadata_in_agent_source(self):
        source=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_shopping_reddit_review_compound.py").read_text()
        for marker in ("task_id","intent_template_id","instantiation_dict","expected_answer","evaluate_task","hard.json"):
            self.assertNotIn(marker,source)

if __name__=="__main__":
    unittest.main()
