"""Tests for the synthetic claim-fidelity separation gate."""

import unittest

from assess_claim_fidelity import require_exact_synthetic_contract, require_lean_witness


CONTRACT = {
    "schema": "nucleus-north-star-synthetic-claim-v1",
    "checked_declaration": "NorthStarClaim.checkedTheorem",
    "checked_type": "∀ (R : Prop), R → R",
    "intended_type": "∀ (R : Prop), R",
    "separation_declaration": "NorthStarClaim.separation",
    "authorization": "SYNTHETIC_CONTROL_ONLY",
}


class TestClaimFidelityBoundary(unittest.TestCase):
    def test_exact_contract_is_experiment_only(self):
        require_exact_synthetic_contract(CONTRACT)

    def test_modified_intent_cannot_inherit_separation_warrant(self):
        altered = {**CONTRACT, "intended_type": "∀ (R : Prop), R → R"}
        with self.assertRaises(AssertionError):
            require_exact_synthetic_contract(altered)

    def test_both_axiom_free_lean_reports_required(self):
        log = (
            "'NorthStarClaim.checkedTheorem' does not depend on any axioms\n"
            "'NorthStarClaim.separation' does not depend on any axioms\n"
        )
        require_lean_witness(log)
        with self.assertRaises(AssertionError):
            require_lean_witness("'NorthStarClaim.checkedTheorem' does not depend on any axioms")

    def test_axiom_dependence_blocks_axiom_free_warrant(self):
        log = (
            "'NorthStarClaim.checkedTheorem' does not depend on any axioms\n"
            "'NorthStarClaim.separation' depends on axioms: [Classical.choice]"
        )
        with self.assertRaises(AssertionError):
            require_lean_witness(log)


if __name__ == "__main__":
    unittest.main()
