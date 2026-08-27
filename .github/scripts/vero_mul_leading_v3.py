from pathlib import Path

src = Path('../.github/scripts/vero_mul_leading_v1.py').read_text()
src = src.replace("source = Path('mul_leading_v1/source').resolve()", "source = Path('mul_leading_v3/source').resolve()")
src = src.replace("outdir=Path('mul_leading_v1')", "outdir=Path('mul_leading_v3')")
src = src.replace("MUL_LEADING_V1_CENSUS", "MUL_LEADING_V3_CENSUS")

src = src.replace(
"""            rw [zipAddPad_length_local] at hl
            simp at hl
            omega
          simp only [Galoistools.zipAddPad]
""",
"""            rw [zipAddPad_length_local] at hl
            simp at hl
            exact hys' (List.length_eq_zero.mp hl)
          simp only [Galoistools.zipAddPad]
""")

src = src.replace(
"""theorem leadCoeff_reverse_eq_last0 (xs : List Nat) (hxs : xs ≠ []) :
    Galoistools.leadCoeff xs.reverse = last0 xs := by
  simpa using (last0_reverse xs.reverse)
""",
"""theorem leadCoeff_reverse_eq_last0 (xs : List Nat) (hxs : xs ≠ []) :
    Galoistools.leadCoeff xs.reverse = last0 xs := by
  simpa using (last0_reverse xs.reverse).symm
""")

exec(compile(src, '.github/scripts/vero_mul_leading_v3_generated.py', 'exec'), {'__name__': '__main__'})
