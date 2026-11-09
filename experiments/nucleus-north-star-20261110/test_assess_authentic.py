"""Protect exact Lean-output presentation versus semantic source identity."""

import unittest

from assess_authentic import lean_axioms


class TestLeanAxiomReadback(unittest.TestCase):
    def test_lean_shortens_names_in_the_current_namespace(self):
        log = "'NorthStar.dependent' depends on axioms: [P, Q, givenQ, implication]"
        self.assertEqual(lean_axioms(log, "NorthStar.dependent"),
                         ["NorthStar.P", "NorthStar.Q", "NorthStar.givenQ", "NorthStar.implication"])

    def test_fully_qualified_or_external_names_are_not_rewritten(self):
        log = "'NorthStar.dependent' depends on axioms: [NorthStar.P, Classical.choice]"
        self.assertEqual(lean_axioms(log, "NorthStar.dependent"),
                         ["Classical.choice", "NorthStar.P"])

    def test_axiom_free_positive_control_remains_empty(self):
        log = "'NorthStar.independent' does not depend on any axioms"
        self.assertEqual(lean_axioms(log, "NorthStar.independent"), [])


if __name__ == "__main__":
    unittest.main()
