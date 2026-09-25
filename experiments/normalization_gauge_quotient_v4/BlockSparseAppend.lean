
/-! MathGraph V4 quotient-factorization probe: block_sparse_attn. -/

namespace VeriTile.Bench.TritonBenchG.BlockSparseAttn

open VeriTile.Triton
open BSAMathCausal
open MathGraphNormalizationQuotient

theorem mathgraph_v4_block_sparse_gauge
    {M D Dv Bk : Nat} (hBk : 0 < Bk)
    (qStart : Nat) (numKVBlocks : Nat) (hN : 0 < numKVBlocks)
    (gpos : Fin (Bk * numKVBlocks) → Nat)
    (Q : TileIndex [M, D] → ℝ)
    (Kg : TileIndex [Bk * numKVBlocks, D] → ℝ)
    (Vg : TileIndex [Bk * numKVBlocks, Dv] → ℝ) (scale0 : ℝ)
    (idx : TileIndex [M, Dv])
    (hVis0 : gpos ⟨0, Nat.mul_pos hBk hN⟩ ≤ qStart + idx.1.val) :
    GaugeEq
      ⟨oFree qStart gpos Q Kg Vg scale0 numKVBlocks (le_refl _) idx,
        lFree qStart gpos Q Kg scale0 numKVBlocks (le_refl _) idx.1⟩
      ⟨bsaOPartial Bk qStart numKVBlocks gpos Q Kg Vg scale0 numKVBlocks idx,
        bsaLPartial Bk qStart numKVBlocks gpos Q Kg scale0 numKVBlocks idx.1⟩ := by
  let c := Real.exp (-(bsaMPartial Bk qStart numKVBlocks gpos Q Kg scale0
    numKVBlocks idx.1).unbotD 0)
  refine ⟨c, Real.exp_ne_zero _, ?_⟩
  apply RatioState.ext
  · exact bsaOPartial_eq_mShifted hBk qStart numKVBlocks hN gpos Q Kg Vg scale0
      numKVBlocks (le_refl _) idx hVis0
  · exact bsaLPartial_eq_mShifted hBk qStart numKVBlocks hN gpos Q Kg scale0
      numKVBlocks (le_refl _) idx.1 hVis0

theorem mathgraph_v4_block_sparse_observation
    {M D Dv Bk : Nat} (hBk : 0 < Bk)
    (qStart : Nat) (numKVBlocks : Nat) (hN : 0 < numKVBlocks)
    (gpos : Fin (Bk * numKVBlocks) → Nat)
    (Q : TileIndex [M, D] → ℝ)
    (Kg : TileIndex [Bk * numKVBlocks, D] → ℝ)
    (Vg : TileIndex [Bk * numKVBlocks, Dv] → ℝ) (scale0 : ℝ)
    (idx : TileIndex [M, Dv])
    (hVis0 : gpos ⟨0, Nat.mul_pos hBk hN⟩ ≤ qStart + idx.1.val) :
    observe
      ⟨bsaOPartial Bk qStart numKVBlocks gpos Q Kg Vg scale0 numKVBlocks idx,
        bsaLPartial Bk qStart numKVBlocks gpos Q Kg scale0 numKVBlocks idx.1⟩
      =
    observe
      ⟨oFree qStart gpos Q Kg Vg scale0 numKVBlocks (le_refl _) idx,
        lFree qStart gpos Q Kg scale0 numKVBlocks (le_refl _) idx.1⟩ :=
  (observe_eq_of_gauge
    (mathgraph_v4_block_sparse_gauge hBk qStart numKVBlocks hN gpos Q Kg Vg
      scale0 idx hVis0)).symm

end VeriTile.Bench.TritonBenchG.BlockSparseAttn
