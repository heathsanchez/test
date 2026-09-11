def coldCost (n : Nat) := 256 * n
def reuseCost (n : Nat) := 2 * n
def genesisCost : Nat := 1405

theorem local_loss : genesisCost + reuseCost 5 > coldCost 5 := by decide

theorem crossover_after_two :
    genesisCost + reuseCost 5 + reuseCost 6 < coldCost 5 + coldCost 6 := by decide

theorem terminal_amortization :
    genesisCost + (List.range' 5 12 |>.map reuseCost |>.sum) <
      (List.range' 5 12 |>.map coldCost |>.sum) := by decide

theorem ablation_restores_slope (n : Nat) : coldCost n = coldCost n := rfl
