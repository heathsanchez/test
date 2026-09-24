
/-! ## MathGraph frozen-capability blind transfer probe

The capability used here was frozen before BlockSparseAttn was selected.
This theorem intentionally does not call the target's existing
`bsaStreaming_eq_bsaAttn`.
-/

namespace VeriTile.Bench.TritonBenchG.BlockSparseAttn

open VeriTile.Triton
open BSAMathCausal

theorem mathgraph_transfer_bsaStreaming_eq_bsaAttn
    {M D Dv Bk : Nat} (hBk : 0 < Bk)
    (qStart : Nat) (numKVBlocks : Nat) (hN : 0 < numKVBlocks)
    (gpos : Fin (Bk * numKVBlocks) → Nat)
    (Q : TileIndex [M, D] → ℝ)
    (Kg : TileIndex [Bk * numKVBlocks, D] → ℝ)
    (Vg : TileIndex [Bk * numKVBlocks, Dv] → ℝ) (scale : ℝ)
    (idx : TileIndex [M, Dv])
    (hVis0 : gpos ⟨0, Nat.mul_pos hBk hN⟩ ≤ qStart + idx.1.val) :
    bsaOPartial Bk qStart numKVBlocks gpos Q Kg Vg scale numKVBlocks idx /
        bsaLPartial Bk qStart numKVBlocks gpos Q Kg scale numKVBlocks idx.1
      = bsaAttn qStart gpos Q Kg Vg scale idx := by
  rw [bsaOPartial_eq_mShifted hBk qStart numKVBlocks hN gpos Q Kg Vg scale numKVBlocks
        (le_refl _) idx hVis0,
      bsaLPartial_eq_mShifted hBk qStart numKVBlocks hN gpos Q Kg scale numKVBlocks
        (le_refl _) idx.1 hVis0]
  calc
    _ = oFree qStart gpos Q Kg Vg scale numKVBlocks (le_refl _) idx /
        lFree qStart gpos Q Kg scale numKVBlocks (le_refl _) idx.1 := by
      exact MathGraphGaugeCapability.common_factor_ratio _ _ _ _ _
        (Real.exp_ne_zero _) rfl rfl
    _ = bsaAttn qStart gpos Q Kg Vg scale idx :=
      oFree_div_lFree_eq_bsaAttn qStart gpos Q Kg Vg scale idx

end VeriTile.Bench.TritonBenchG.BlockSparseAttn
