
/-! MathGraph V4 quotient-factorization probe: mixed_sparse_attention. -/

namespace VeriTile.Bench.TritonBenchG.MixedSparseAttention

open MathGraphNormalizationQuotient

theorem mathgraph_v4_mixed_sparse_gauge
    (BM BN BD : Nat) (score) (vblk) (k : Nat)
    (i : Fin BM) (d : Fin BD)
    (hpos : 0 < msaDenomUpto BM BN score k i) :
    GaugeEq
      ⟨msaOPartial BM BN BD score vblk k i d,
        msaLPartial BM BN score k i⟩
      ⟨msaNumerUpto BM BN BD score vblk k i d,
        msaDenomUpto BM BN score k i⟩ := by
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
  refine ⟨msaE (msaMPartial BM BN score k i), ne_of_gt hEpos, ?_⟩
  apply RatioState.ext
  · exact hO.symm
  · exact hL.symm

theorem mathgraph_v4_mixed_sparse_observation
    (BM BN BD : Nat) (score) (vblk) (k : Nat)
    (i : Fin BM) (d : Fin BD)
    (hpos : 0 < msaDenomUpto BM BN score k i) :
    observe
      ⟨msaOPartial BM BN BD score vblk k i d,
        msaLPartial BM BN score k i⟩
      =
    observe
      ⟨msaNumerUpto BM BN BD score vblk k i d,
        msaDenomUpto BM BN score k i⟩ :=
  observe_eq_of_gauge
    (mathgraph_v4_mixed_sparse_gauge BM BN BD score vblk k i d hpos)

end VeriTile.Bench.TritonBenchG.MixedSparseAttention
