import Collatz.EventualMacroProgress

namespace CollatzFinal.SourceProduct

-- These are the 105 observed layer edges, not a universal transition model.
def protectedObservedLayerEdges : List (Nat × Nat) := [(1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2), (4, 0), (4, 1), (4, 2), (4, 3), (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 6), (8, 0), (8, 1), (8, 2), (8, 3), (8, 5), (8, 6), (8, 7), (9, 0), (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (9, 8), (10, 0), (10, 1), (10, 3), (10, 6), (10, 7), (10, 9), (11, 0), (11, 1), (11, 2), (11, 3), (11, 4), (11, 7), (11, 10), (12, 0), (12, 1), (12, 3), (12, 4), (12, 5), (12, 11), (13, 0), (13, 1), (13, 2), (13, 3), (13, 4), (13, 5), (13, 6), (13, 9), (13, 12), (14, 1), (14, 2), (14, 3), (14, 5), (14, 10), (14, 13), (15, 1), (15, 3), (15, 10), (15, 14), (16, 0), (16, 1), (16, 2), (16, 5), (16, 8), (16, 13), (16, 15), (17, 1), (17, 4), (17, 16), (18, 12), (18, 17), (19, 1), (19, 6), (19, 18), (20, 19), (21, 20), (22, 5), (22, 21), (23, 22), (24, 0), (24, 23), (25, 24), (26, 25), (27, 26), (28, 27)]

def protectedObservedLayerChecks : Bool :=
  protectedObservedLayerEdges.all (fun e => decide (e.2 < e.1))

theorem protected_observed_layer_edges_decrease :
    protectedObservedLayerChecks = true := by decide

-- The universal simulation premise remains open. The bounded edge check above
-- does not discharge it; this theorem only exposes the exact formal seam.
theorem collatz_of_universal_protected_future_simulation
    (rank : State → Nat)
    (hcoverage : ∀ s, ZeroTailLive s → ∃ j,
      (¬ Live (iter step j s)) ∨
      (ZeroTailLive (iter step j s) ∧
       rank (iter step j s) < rank s)) :
    ∀ n, 0 < n → CollatzGood n := by
  exact collatz_of_zero_tail_eventual_progress_or_exit
    (fun s : State => s) rank hcoverage

#print axioms protected_observed_layer_edges_decrease
#print axioms collatz_of_universal_protected_future_simulation

end CollatzFinal.SourceProduct
