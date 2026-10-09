"""Fail-closed catalog names; examples captured in Hard run 37974659680."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

class ProductNameSelection(unittest.TestCase):
    def test_five_distinct_partial_product_names(self):
        from webarena_product_name_match import select_observed_product
        cases=[
            ('Sony Computer Entertainment VR',
             'Sony Computer Entertainment VR - Worlds Bundle - PlayStation 4',
             'Sony PlayStation VR Headset and Accessories Carrying Case'),
            ('Nintendo Switch Fortnite Wildcat Console EU',
             'Nintendo Switch Fortnite Wildcat Console (Eu Version) - Switch',
             'Nintendo Joy-Con (L)/(R) Fortnite Fleet Force Bundle - Nintendo Switch'),
            ('Racing Wheel Overdrive for Xbox X',
             'Racing Wheel Overdrive Designed for Xbox Series X|S By HORI - Officially Licensed by Microsoft',
             'Game Racing Wheel, PXN-V3II 180 degree Competition Racing Steering Wheel'),
            ('Doc and Pies Arcade Factory Cocktail Arcade Machine',
             'Doc and Pies Arcade Factory Cocktail Arcade Machine - 60 Retro Games - Full Size LCD Screen',
             'Creative Arcades Set of 2 Swivel Bar Stools'),
            ('HORI 3D Surround Gaming Neckset',
             'HORI 3D Surround Gaming Neckset - Wearable Speaker with Voice Chat Designed for Xbox Series X|S',
             'Audeze Mobius Premium 3D Gaming Headset with Surround Sound'),
        ]
        for requested,correct,distractor in cases:
            with self.subTest(request=requested):
                candidates=[{'name':correct,'url':'http://localhost:7770/correct.html'},
                            {'name':distractor,'url':'http://localhost:7770/other.html'}]
                selected=select_observed_product(requested,candidates)
                self.assertEqual(selected['url'],candidates[0]['url'])

    def test_ambiguous_variants_fail_closed(self):
        from webarena_product_name_match import select_observed_product
        with self.assertRaises(RuntimeError):
            select_observed_product('iphone 12 protective case',[
                {'name':'iPhone 12 Protective Case Red','url':'http://localhost:7770/a.html'},
                {'name':'iPhone 12 Protective Case Blue','url':'http://localhost:7770/b.html'}])

    def test_unrelated_item_not_accepted(self):
        from webarena_product_name_match import select_observed_product
        with self.assertRaises(RuntimeError):
            select_observed_product('Sony Computer Entertainment VR',[
                {'name':'Sony Controller and Console','url':'http://localhost:7770/other.html'}])

    def test_no_hardcoded_task_metadata(self):
        src=(ROOT/'scripts/webarena_product_name_match.py').read_text()
        for forbidden in ('task_id','intent_template_id','instantiation_dict','expected_answer','evaluate_task'):
            self.assertNotIn(forbidden,src)

if __name__=='__main__':unittest.main()
