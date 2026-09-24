
/-! ## MathGraph cross-family gauge-cancellation probe

This theorem is appended only in the ephemeral CI checkout. It intentionally
does not invoke the file's existing `msaPartial_ratio_collapse`. The
MixedSparseAttention-specific recurrence and max/exp2 facts stay local; only
the final common-factor cancellation is supplied by the compiled capability.
-/

namespace VeriTile.Bench.TritonBenchG.MixedSparseAttention

theorem mathgraph_transfer_msaPartial_ratio_collapse
    (BM BN BD : Nat) (score) (vblk) (k : Nat)
    (i : Fin BM) (d : Fin BD)
    (hpos : 0 < msaDenomUpto BM BN score k i) :
    msaOPartial BM BN BD score vblk k i d / msaLPartial BM BN score k i
      = msaNumerUpto BM BN BD score vblk k i d / msaDenomUpto BM BN score k i := by
  have hL := msaLPartial_collapse BM BN score k i
  have hO := msaOPartial_collapse BM BN BD score vblk k i d
  have hEpos : 0 < msaE (msaMPartial BM BN score k i) := by
    cases hm : msaMPartial BM BN score k i with
    | bot =>
      exfalso
      rw [hm] at hL
      simp only [msaE_bot, zero_mul] at hL
      rw [← hL] at hpos
      exact lt_irrefl 0 hpos
    | coe r =>
      show 0 < msaE (some r)
      rw [msaE_some]
      exact Real.exp_pos _
  exact MathGraphGaugeCapability.common_factor_ratio
    (msaE (msaMPartial BM BN score k i))
    (msaOPartial BM BN BD score vblk k i d)
    (msaLPartial BM BN score k i)
    (msaNumerUpto BM BN BD score vblk k i d)
    (msaDenomUpto BM BN score k i)
    (ne_of_gt hEpos) hO hL

end VeriTile.Bench.TritonBenchG.MixedSparseAttention
