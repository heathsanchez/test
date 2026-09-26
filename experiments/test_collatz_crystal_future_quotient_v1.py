import unittest

import collatz_crystal_future_quotient_v1 as fq


class FutureQuotientCoreTests(unittest.TestCase):
    def test_future_equivalent_presentation_states_merge(self):
        nodes = {"depth7:rungA", "depth99:rungZ", "exit"}
        succ = {
            "depth7:rungA": {"exit"},
            "depth99:rungZ": {"exit"},
            "exit": set(),
        }
        classes, qnodes, qsucc, qexits = fq.refine_future_quotient(
            nodes, succ, {"exit"})
        self.assertEqual(classes["depth7:rungA"], classes["depth99:rungZ"])
        self.assertNotEqual(classes["depth7:rungA"], classes["exit"])

    def test_recurrent_cycle_survives_greatest_kernel(self):
        nodes = {"a", "b", "dead"}
        succ = {"a": {"b"}, "b": {"a"}, "dead": set()}
        kernel = fq.greatest_kernel(nodes, succ)
        self.assertEqual(kernel, {"a", "b"})

    def test_rank_if_acyclic_decreases_on_every_edge(self):
        nodes = {"top", "mid", "leaf"}
        succ = {"top": {"mid"}, "mid": {"leaf"}, "leaf": set()}
        rank = fq.rank_if_acyclic(nodes, succ)
        self.assertIsNotNone(rank)
        for s in nodes:
            for t in succ[s]:
                self.assertLess(rank[t], rank[s])

    def test_rank_if_acyclic_rejects_cycle(self):
        nodes = {"a", "b"}
        succ = {"a": {"b"}, "b": {"a"}}
        self.assertIsNone(fq.rank_if_acyclic(nodes, succ))


if __name__ == "__main__":
    unittest.main()
