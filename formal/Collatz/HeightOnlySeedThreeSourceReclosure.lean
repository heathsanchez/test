import Collatz.HeightClockEliminationMonotonicity

namespace CollatzFinal
namespace SourceProduct

set_option maxRecDepth 8192
set_option maxHeartbeats 1000000

/-!
V175 — ONE HEIGHT-ADMITTED TERMINAL SEED CLOSES THREE
EARLIER UNSEEDED ORIGINAL-SOURCE MEMBERS.

This is an explicit actual integer source-and-clock evidence packet.
The three old sources n1=10,723,327, n2=16,084,991,
n3=14,297,769 all lie below 2^24. At H=200 and the smaller
source cutoff, V174's full finite graph leaves these three
in ONE unseeded component (BOUNDED exact audit, not asserted
as a Lean universal negative).

After enlarging SOURCE HEIGHT ONLY to 2^25, a single new
original source p=23,311,879 supplies a REAL terminal seed:

  T(n1)=n2,
  T^2(n3)=n1,
  T^198(n2)=T^2(p)=52,451,729,
  T^68(p)=2.

Every source/clock equality is independently decidable and
the complete actual finite canonical graph proof is below.
All edges/terminal-seed clocks <= H=200.

The seed is LARGER than all three older sources, so it is
NOT an earlier-source induction certificate (V131/V134).
The source-window increase is the crucial enabling move.

The finite proof composes to exact terminal clocks
  T^264(n2)=2; T^265(n1)=2; T^267(n3)=2.
No all-scale component contraction, all-positive convergence,
or Collatz QED is claimed.

The new finite proof is an instance of V168's universally
sound retroactive future-path compiler, not an assumption
that every unresolved component eventually receives a seed.
-/

def v175Root : Nat := 23311879
def v175N1 : Nat := 10723327
def v175N2 : Nat := 16084991
def v175N3 : Nat := 14297769

theorem v175_actual_original_source_window :
    v175N1 < 2^24 ∧ v175N2 < 2^24 ∧
    v175N3 < 2^24 ∧
    2^24 ≤ v175Root ∧ v175Root < 2^25 := by
  decide

theorem v175_old_component_first_short_link :
    shortcut v175N1 = v175N2 := by
  decide

theorem v175_old_component_second_short_link :
    iter shortcut 2 v175N3 = v175N1 := by
  decide

theorem v175_new_source_true_two_clock_join :
    iter shortcut 198 v175N2 =
    iter shortcut 2 v175Root := by
  decide

theorem v175_join_reached_endpoint :
    iter shortcut 2 v175Root = 52451729 := by
  decide

theorem v175_new_source_true_terminal_seed :
    iter shortcut 68 v175Root = 2 := by
  decide

theorem v175_terminal_n2_from_new_larger_seed :
    iter shortcut 264 v175N2 = 2 := by
  calc
    iter shortcut 264 v175N2 =
        iter shortcut (198+66) v175N2 := by
          rfl
    _ = iter shortcut 66 (iter shortcut 198 v175N2) :=
      iter_add shortcut 198 66 v175N2
    _ = iter shortcut 66 (iter shortcut 2 v175Root) := by
      rw [v175_new_source_true_two_clock_join]
    _ = iter shortcut 68 v175Root := by
      have h := iter_add shortcut 2 66 v175Root
      simpa only [show (2:Nat)+66=68 by decide] using h.symm
    _ = 2 := v175_new_source_true_terminal_seed

theorem v175_terminal_n1_by_proof_reuse :
    iter shortcut 265 v175N1 = 2 := by
  calc
    iter shortcut 265 v175N1 =
        iter shortcut (1+264) v175N1 := by rfl
    _ = iter shortcut 264 (iter shortcut 1 v175N1) :=
      iter_add shortcut 1 264 v175N1
    _ = iter shortcut 264 v175N2 := by
      change iter shortcut 264 (shortcut v175N1) =
        iter shortcut 264 v175N2
      rw [v175_old_component_first_short_link]
    _ = 2 := v175_terminal_n2_from_new_larger_seed

theorem v175_terminal_n3_by_proof_reuse :
    iter shortcut 267 v175N3 = 2 := by
  calc
    iter shortcut 267 v175N3 =
        iter shortcut (2+265) v175N3 := by rfl
    _ = iter shortcut 265 (iter shortcut 2 v175N3) :=
      iter_add shortcut 2 265 v175N3
    _ = iter shortcut 265 v175N1 := by
      rw [v175_old_component_second_short_link]
    _ = 2 := v175_terminal_n1_by_proof_reuse

/-- A REAL full canonical H=200 / X=2^25 source graph path.
    This edge is ABSENT at cutoff X=2^24 because the new source
    p is not in the original vertex set. -/
theorem v175_new_shell_actual_edge :
    V170FullClockPath (2^25) 200 v175N2 v175Root := by
  apply V170FullClockPath.meeting (i:=198) (j:=2)
  · decide
  · decide
  · decide
  · decide
  · decide
  · decide
  · exact v175_new_source_true_two_clock_join

theorem v175_old_actual_short_edge_1 :
    V170FullClockPath (2^25) 200 v175N1 v175N2 := by
  apply V170FullClockPath.meeting (i:=1) (j:=0)
  · decide
  · decide
  · decide
  · decide
  · decide
  · decide
  · simpa only [iter] using v175_old_component_first_short_link

theorem v175_old_actual_short_edge_2 :
    V170FullClockPath (2^25) 200 v175N3 v175N1 := by
  apply V170FullClockPath.meeting (i:=2) (j:=0)
  · decide
  · decide
  · decide
  · decide
  · decide
  · decide
  · simpa only [iter] using v175_old_component_second_short_link

theorem v175_old_three_share_single_new_shell_seed :
    V170HasTerminalSeed (2^25) 200 v175N1 ∧
    V170HasTerminalSeed (2^25) 200 v175N2 ∧
    V170HasTerminalSeed (2^25) 200 v175N3 := by
  have hN2 : V170HasTerminalSeed (2^25) 200 v175N2 := by
    exact ⟨v175Root,by decide,by decide,
      v175_new_shell_actual_edge,
      68,by decide,Or.inr v175_new_source_true_terminal_seed⟩
  have hN1 : V170HasTerminalSeed (2^25) 200 v175N1 := by
    exact ⟨v175Root,by decide,by decide,
      V170FullClockPath.compose
        v175_old_actual_short_edge_1 v175_new_shell_actual_edge,
      68,by decide,Or.inr v175_new_source_true_terminal_seed⟩
  have hN3 : V170HasTerminalSeed (2^25) 200 v175N3 := by
    exact ⟨v175Root,by decide,by decide,
      V170FullClockPath.compose
        v175_old_actual_short_edge_2
        (V170FullClockPath.compose
          v175_old_actual_short_edge_1
          v175_new_shell_actual_edge),
      68,by decide,Or.inr v175_new_source_true_terminal_seed⟩
  exact ⟨hN1,hN2,hN3⟩

theorem v175_all_three_true_collatz_good :
    CollatzGood v175N1 ∧
    CollatzGood v175N2 ∧
    CollatzGood v175N3 := by
  obtain ⟨h1,h2,h3⟩ :=
    v175_old_three_share_single_new_shell_seed
  exact ⟨v170_terminal_seeded_class_is_good _ _ _ h1,
    v170_terminal_seeded_class_is_good _ _ _ h2,
    v170_terminal_seeded_class_is_good _ _ _ h3⟩

#print axioms v175_actual_original_source_window
#print axioms v175_old_component_first_short_link
#print axioms v175_old_component_second_short_link
#print axioms v175_new_source_true_two_clock_join
#print axioms v175_join_reached_endpoint
#print axioms v175_new_source_true_terminal_seed
#print axioms v175_terminal_n2_from_new_larger_seed
#print axioms v175_terminal_n1_by_proof_reuse
#print axioms v175_terminal_n3_by_proof_reuse
#print axioms v175_new_shell_actual_edge
#print axioms v175_old_actual_short_edge_1
#print axioms v175_old_actual_short_edge_2
#print axioms v175_old_three_share_single_new_shell_seed
#print axioms v175_all_three_true_collatz_good

end SourceProduct
end CollatzFinal
