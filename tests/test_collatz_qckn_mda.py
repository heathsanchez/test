import unittest

from collatz_qckn.mda import licensed_interventions, select_intervention
from collatz_qckn.types import Intervention, Outcome


class MDATest(unittest.TestCase):
    def test_certified_descent_licenses_compile(self):
        self.assertEqual(licensed_interventions(Outcome.CERTIFIED_DESCENT),(Intervention.COMPILE,))

    def test_rigid_residual_licenses_construct_verify_restructure(self):
        got=set(licensed_interventions(Outcome.RIGID_RESIDUAL))
        self.assertTrue({Intervention.CONSTRUCT,Intervention.VERIFY,Intervention.RESTRUCTURE}<=got)

    def test_unknown_search_does_not_license_expand(self):
        self.assertNotIn(Intervention.EXPAND,licensed_interventions(Outcome.UNKNOWN_SEARCH))

    def test_unknown_expressivity_requires_matching_completeness_certificate(self):
        self.assertNotIn(Intervention.EXPAND,
            licensed_interventions(Outcome.UNKNOWN_EXPRESSIVITY,obligation_id="o1"))
        cert={"obligation_id":"o1","complete":True,"no_resolution":True}
        self.assertIn(Intervention.EXPAND,
            licensed_interventions(Outcome.UNKNOWN_EXPRESSIVITY,cert,"o1"))
        self.assertNotIn(Intervention.EXPAND,
            licensed_interventions(Outcome.UNKNOWN_EXPRESSIVITY,cert,"other"))

    def test_selection_uses_lowest_declared_cost(self):
        got=select_intervention(Outcome.RIGID_RESIDUAL,{
            Intervention.CONSTRUCT:5,Intervention.VERIFY:2,Intervention.RESTRUCTURE:9})
        self.assertEqual(got,Intervention.VERIFY)


if __name__=="__main__":
    unittest.main()
