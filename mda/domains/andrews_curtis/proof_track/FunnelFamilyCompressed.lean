import OrbitSoundness
import FunnelCore

/-!
# The mined funnel family as a one-line instance of the universal law

The original constructive proof exposed the mechanism.  This file checks the
compression: the entire m-parameter is just one removable twist of the simpler
base presentation `(y, y^{-k} x^{-1})`.
-/

namespace AC

/-- The two-parameter mined family is a single commutator-twist orbit of the
one-parameter base family. -/
theorem funnelFamily_to_base_by_one_twist (m k : ℕ) :
    Reachable (funnelRelators m k)
      (![funnelY, funnelB k] : Relators 2) := by
  let R : Relators 2 := ![funnelY, funnelB k]
  let w : Word 2 := (funnelY⁻¹)^m

  have h :=
    commutatorTwist_contract R
      (0 : Fin 2) (1 : Fin 2) (by decide) w

  have hstart :
      Function.update R (0 : Fin 2)
        ((R (1 : Fin 2))⁻¹ * w * R (1 : Fin 2) * w⁻¹ * R (0 : Fin 2))
        = funnelRelators m k := by
    funext q
    fin_cases q
    · simp [R, w, funnelRelators, funnelA, funnelB]
      group
    · simp [R, funnelRelators]

  rw [hstart] at h
  simpa [R] using h

/-- Compressed proof of the full infinite family.

The m-complexity disappears into one application of the universal twist law;
only the elementary k-tail remains.
-/
theorem funnelFamily_reachable_compressed (m k : ℕ) :
    Reachable (funnelRelators m k) (standard 2) := by
  have htw :
      Reachable (funnelRelators m k)
        (![funnelY, funnelB k] : Relators 2) :=
    funnelFamily_to_base_by_one_twist m k

  have hk :
      Reachable (![funnelY, funnelB k] : Relators 2)
        (![funnelY, funnelX⁻¹] : Relators 2) :=
    funnel_eliminate_k k

  have hinvStep :
      Step (![funnelY, funnelX⁻¹] : Relators 2)
        (Function.update (![funnelY, funnelX⁻¹] : Relators 2)
          (1 : Fin 2) funnelX) := by
    simpa using Step.inv (![funnelY, funnelX⁻¹] : Relators 2) (1 : Fin 2)

  have hinv :
      Reachable (![funnelY, funnelX⁻¹] : Relators 2)
        (![funnelY, funnelX] : Relators 2) := by
    have h0 := step_reachable hinvStep
    rw [funnel_update_one] at h0
    exact h0

  have hswap :=
    relatorSwap_reachable (![funnelY, funnelX] : Relators 2)
      (0 : Fin 2) (1 : Fin 2) (by decide)

  have htarget :
      swapRelators (![funnelY, funnelX] : Relators 2)
        (0 : Fin 2) (1 : Fin 2) = standard 2 := by
    funext q
    fin_cases q <;> simp [swapRelators, funnelX, funnelY, standard]

  rw [htarget] at hswap
  exact htw.trans (hk.trans (hinv.trans hswap))

end AC
