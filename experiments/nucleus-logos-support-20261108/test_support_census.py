import unittest

from support_census import SourceGraph


class SourceSupportTests(unittest.TestCase):
    def test_open_and_bound_bvars_are_distinct(self):
        graph = SourceGraph.from_rows([
            {"ie": 0, "bvar": 0},
            {"ie": 1, "bvar": 1},
            {"ie": 2, "sort": 0},
            {"ie": 3, "lam": {"type": 2, "body": 0}},
            {"ie": 4, "lam": {"type": 2, "body": 1}},
            {"ie": 5, "app": {"fn": 3, "arg": 4}},
        ])
        self.assertEqual(graph.support(3), ())
        self.assertEqual(graph.support(4), (0,))
        self.assertEqual(graph.support(5), (0,))

    def test_let_projections_and_nested_binders(self):
        graph = SourceGraph.from_rows([
            {"ie": 1, "bvar": 2},
            {"ie": 2, "const": {"name": 1, "us": []}},
            {"ie": 3, "letE": {"type": 2, "value": 2, "body": 1}},
            {"ie": 4, "proj": {"struct": 3, "typeName": 1, "idx": 0}},
            {"ie": 5, "forallE": {"type": 2, "body": 4}},
        ])
        self.assertEqual(graph.support(3), (1,))
        self.assertEqual(graph.support(4), (1,))
        self.assertEqual(graph.support(5), (0,))

    def test_missing_or_cyclic_nodes_fail_closed(self):
        self.assertIsNone(SourceGraph.from_rows([
            {"ie": 1, "app": {"fn": 1, "arg": 1}},
        ]).support(1))
        self.assertIsNone(SourceGraph.from_rows([
            {"ie": 1, "app": {"fn": 9, "arg": 9}},
        ]).support(1))

    def test_metadata_does_not_create_a_false_source(self):
        graph = SourceGraph.from_rows([
            {"meta": {"format": {"version": "3.1.0"}}},
            {"ie": 1, "natVal": "37"},
        ])
        self.assertEqual(len(graph.nodes), 1)
        self.assertEqual(graph.support(1), ())


if __name__ == "__main__":
    unittest.main()
