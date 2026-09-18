import unittest
from collatz_flash import Graph, contract


class FlashTests(unittest.TestCase):
    def test_scope_does_not_cancel_symbolic_work(self):
        graph = Graph([contract(), dict(contract(), execution='symbolic')])
        graph.admit('reviewed-dominance-v1')
        self.assertEqual(graph.states, ['blocked', 'pending'])

    def test_revocation_reopens_dependent_work(self):
        graph = Graph([contract()])
        graph.admit('reviewed-dominance-v1')
        graph.revoke()
        self.assertEqual(graph.states, ['pending'])

    def test_unknown_authority_cannot_change_state(self):
        graph = Graph([contract()])
        with self.assertRaises(ValueError): graph.admit('benchmark-only')
        self.assertEqual(graph.states, ['pending'])

    def test_wrong_metric_not_blocked(self):
        graph = Graph([dict(contract(), metric='wall_seconds')])
        graph.admit('reviewed-dominance-v1')
        self.assertEqual(graph.states, ['pending'])


if __name__ == '__main__': unittest.main()
