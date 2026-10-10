import Collatz.DensityAmplificationClosure
import Collatz.ClockedGiantComponentBridge

namespace CollatzFinal
namespace SourceProduct

/-!
V170 — ELIMINATE A SECOND MACROSCOPIC FUTURE COMPONENT.

The source-locked graph needs only GENUINE two-clock endpoint equality.
Terminal status is irrelevant to the quantitative uniqueness condition.

This formal theorem is CONDITIONAL: timed targetwise shortcut-predecessor
density (external WordCertDensity/Shaik, not locally imported), source-
complete clocked ledgers, and sparse uniqueness of a macroscopic
component are THREE explicit obligations. None is silently discharged.

True Collatz remains UNKNOWN; no QED is claimed.
-/

/-- Full observed genuine two-clock component, even if no member has
a terminal certificate. Members are ORIGINAL positive sources below X. -/
noncomputable def V170ComponentCount
    (edges : List V168TwoClockEdge) (b X : Nat) : Nat := by
  classical
  exact v150Count (fun n => 0 < n ∧ V168Path edges n b) X

/-- Positive shortcuts hitting target b within H actual source clocks. -/
noncomputable def V170TimedCount (b H X : Nat) : Nat := by
  classical
  exact v150Count (fun n => 0 < n ∧ V169HitWithin n b H) X

/-- Source-complete future-component receipts: every in-range source
whose real orbit hits an in-range target by H is linked to that target
by stored, genuinely checked two-clock graph edges. -/
def V170CompleteLedger
    (E : Nat → List V168TwoClockEdge) (H : Nat → Nat) : Prop :=
  ∀ k b : Nat, 0 < b → b < 2^k →
    ∀ n : Nat, 0 < n → n < 2^k →
      V169HitWithin n b (H k) → V168Path (E k) n b

/-- External targetwise time-controlled density in the SHORTCUT
convention. Source import and ordinary-clock conversion (V169 parallel)
are separate declared dependencies, not built here. -/
def V170TimedDensity (H : Nat → Nat) : Prop :=
  ∀ b : Nat, b % 3 = 2 →
    ∃ q X0 : Nat, 0 < q ∧
      ∀ k : Nat, X0 ≤ 2^k →
        2^k ≤ q * V170TimedCount b (H k) (2^k)

/-- Candidate anti-two-giant law. No need to know in advance which
component is terminal. At SOME arbitrarily high dyadic scale, any
two genuinely disconnected future components cannot BOTH contain
at least 2^k/q original positive sources.

This sparse existence formulation is NOT independently proved. -/
def V170SparseNoTwoGiants
    (E : Nat → List V168TwoClockEdge) : Prop :=
  ∀ q X0 : Nat, 0 < q →
    ∃ k : Nat, X0 ≤ 2^k ∧
      ∀ b c : Nat,
        0 < b → b < 2^k → 0 < c → c < 2^k →
        ¬ V168Path (E k) b c →
        q * V170ComponentCount (E k) b (2^k) < 2^k ∨
        q * V170ComponentCount (E k) c (2^k) < 2^k

/-- A genuine bounded target hit is counted in its observed component,
provided the source/clock receipt is actually present. -/
theorem v170_clocked_hits_are_component_members
    (E : List V168TwoClockEdge)
    (b H X : Nat)
    (hComplete : ∀ n, 0 < n → n < X →
      V169HitWithin n b H → V168Path E n b) :
    V170TimedCount b H X ≤ V170ComponentCount E b X := by
  classical
  change v150Count (fun n => 0 < n ∧ V169HitWithin n b H) X ≤
    v150Count (fun n => 0 < n ∧ V168Path E n b) X
  apply v150_count_monotone_below
  intro n hn hHit
  exact ⟨hHit.1, hComplete n hHit.1 hn hHit.2⟩

/-- In the authentic Collatz system, a genuinely bad target cannot
share a checked future-component path with 2 (the known terminal seed). -/
theorem v170_bad_target_not_connected_to_two
    (E : List V168TwoClockEdge) (b : Nat)
    (hBad : ¬ CollatzGood b) :
    ¬ V168Path E b 2 := by
  intro hPath
  have hGoodTwo : CollatzGood 2 := by
    refine ⟨0, ?_⟩
    simp [iter, Terminal]
  have hTwoOne : V155FutureMeet 2 1 :=
    (v155_future_meets_one_iff_good 2).mpr hGoodTwo
  have hMeet : V155FutureMeet b 1 :=
    v155_future_meet_trans (v168_path_sound E hPath) hTwoOne
  exact hBad ((v155_future_meets_one_iff_good b).mp hMeet)

/-- CONDITIONAL QED BRIDGE, not Collatz QED.
Timed density supplies two macroscopic distinct genuine future
components (target 2 and a minimal-bad-source successor b%3=2);
the independent sparse-no-two-giant hypothesis eliminates them.

The source-complete graph and timed-density hypotheses remain explicit.
There is no all-scale spectral gap, no assumed terminal hitting for bad
sources, and no hidden global convergence oracle. -/
theorem v170_collatz_of_timed_density_and_sparse_unique_giant
    (H : Nat → Nat)
    (E : Nat → List V168TwoClockEdge)
    (hDensity : V170TimedDensity H)
    (hComplete : V170CompleteLedger E H)
    (hUnique : V170SparseNoTwoGiants E) :
    ∀ n : Nat, 0 < n → CollatzGood n := by
  have hNoMin : ∀ m : Nat, ¬ MinimalBad PositiveBad m := by
    intro m hMin
    obtain ⟨hBadB, hModB⟩ :=
      v150_minimal_bad_has_nonthree_bad_successor hMin
    let b := shortcut m
    obtain ⟨qTwo, XTwo, hqTwo, hTwoLower⟩ :=
      hDensity 2 (by decide)
    obtain ⟨qB, XB, hqB, hBLower⟩ :=
      hDensity b hModB
    let q := max qTwo qB
    have hq : 0 < q := by
      have hle : qTwo ≤ q := Nat.le_max_left _ _
      omega
    obtain ⟨k, hX, hSep⟩ :=
      hUnique q (XTwo + XB + b + 4) hq
    have hTwoBound : 2 < 2^k := by omega
    have hbBound : b < 2^k := by omega
    have hXTwo : XTwo ≤ 2^k := by omega
    have hXB : XB ≤ 2^k := by omega
    have hMassTwo :=
      v170_clocked_hits_are_component_members
        (E k) 2 (H k) (2^k)
        (hComplete k 2 (by omega) hTwoBound)
    have hMassB :=
      v170_clocked_hits_are_component_members
        (E k) b (H k) (2^k)
        (hComplete k b hBadB.1 hbBound)
    have hLowTwo : 2^k ≤ q * V170ComponentCount (E k) 2 (2^k) := by
      calc
        2^k ≤ qTwo * V170TimedCount 2 (H k) (2^k) :=
          hTwoLower k hXTwo
        _ ≤ q * V170TimedCount 2 (H k) (2^k) :=
          Nat.mul_le_mul_right _ (Nat.le_max_left _ _)
        _ ≤ q * V170ComponentCount (E k) 2 (2^k) :=
          Nat.mul_le_mul_left _ hMassTwo
    have hLowB : 2^k ≤ q * V170ComponentCount (E k) b (2^k) := by
      calc
        2^k ≤ qB * V170TimedCount b (H k) (2^k) :=
          hBLower k hXB
        _ ≤ q * V170TimedCount b (H k) (2^k) :=
          Nat.mul_le_mul_right _ (Nat.le_max_right _ _)
        _ ≤ q * V170ComponentCount (E k) b (2^k) :=
          Nat.mul_le_mul_left _ hMassB
    have hDistinct :=
      v170_bad_target_not_connected_to_two (E k) b hBadB.2
    have hSmall :=
      hSep b 2 hBadB.1 hbBound (by omega) hTwoBound hDistinct
    rcases hSmall with hSmallB | hSmallTwo
    · omega
    · omega
  have hNoBad := no_bad_of_no_minimal PositiveBad hNoMin
  intro n hn
  apply Classical.byContradiction
  intro hBad
  exact hNoBad n ⟨hn, hBad⟩

#print axioms v170_clocked_hits_are_component_members
#print axioms v170_bad_target_not_connected_to_two
#print axioms v170_collatz_of_timed_density_and_sparse_unique_giant

end SourceProduct
end CollatzFinal
