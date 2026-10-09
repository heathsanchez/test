import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_shopping_price_filter_blind import parse_intent

class BlindPriceFilter(unittest.TestCase):
    def test_natural_language_queries(self):
        examples={
            'Open the "women shoes" category page filtered to under $25':("women shoes","25"),
            'Open the "makeup remover" category page filtered to under $46.99':("makeup remover","46.99"),
            'Open the "furniture with accent" category page filtered to under $199':("furniture with accent","199"),
        }
        for intent,(category,cap) in examples.items():
            self.assertEqual(parse_intent(intent),{"category":category,"price_cap":cap})

    def test_reject_unsupported_intents(self):
        with self.assertRaises(ValueError):
            parse_intent("Buy any product under $25")

    def test_blind_metadata_separation(self):
        src=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_shopping_price_filter_blind.py").read_text()
        for term in ("task_id","intent_template_id","instantiation_dict","evaluate_task","expected_answer"):
            self.assertNotIn(term,src)

if __name__=="__main__":
    unittest.main()
