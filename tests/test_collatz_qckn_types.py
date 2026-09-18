import json
import unittest

from collatz_qckn.types import (
    Capability,
    CapabilityKind,
    CostRecord,
    Outcome,
    canonical_json,
    digest_payload,
)


class TypesTest(unittest.TestCase):
    def make_cap(self, provenance="g1", search=3):
        return Capability(
            kind=CapabilityKind.FORWARD_DESCENT_MACRO,
            start_anchor=1,
            end_anchor=2,
            affine_a=9,
            affine_b=7,
            affine_d=4,
            guard_digest="guard",
            contract_digest="contract",
            payload={"word": [[1, 1, 2]], "path_min_delta": -2},
            dependencies=(),
            provenance=provenance,
            cost=CostRecord(search_expansions=search, verifications=1),
        )

    def test_canonical_json_is_order_independent(self):
        a={"z": 1, "a": {"y": 2, "x": 3}}
        b={"a": {"x": 3, "y": 2}, "z": 1}
        self.assertEqual(canonical_json(a), canonical_json(b))
        self.assertEqual(digest_payload(a), digest_payload(b))

    def test_semantic_identity_ignores_provenance_and_cost(self):
        self.assertEqual(
            self.make_cap("g1", 3).semantic_id,
            self.make_cap("g9", 999).semantic_id,
        )

    def test_payload_digest_distinguishes_conflicting_payload(self):
        a=self.make_cap()
        b=Capability(**{**a.as_dict(), "payload": {"word": [[1, 1, 2]], "path_min_delta": -3}})
        self.assertEqual(a.semantic_id,b.semantic_id)
        self.assertNotEqual(a.payload_digest,b.payload_digest)

    def test_outcome_has_unknown_search(self):
        self.assertEqual(Outcome.UNKNOWN_SEARCH.value,"UNKNOWN_SEARCH")


if __name__=="__main__":
    unittest.main()
