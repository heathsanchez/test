from pathlib import Path

src = Path('../.github/scripts/vero_mul_leading_v1.py').read_text()
src = src.replace("source = Path('mul_leading_v1/source').resolve()", "source = Path('mul_leading_v3/source').resolve()")
src = src.replace("outdir=Path('mul_leading_v1')", "outdir=Path('mul_leading_v3')")
src = src.replace("MUL_LEADING_V1_CENSUS", "MUL_LEADING_V3_CENSUS")

src = src.replace(
"""          have htail : Galoistools.zipAddPad p xs ys ≠ [] := by
            intro hz
            have hl := congrArg List.length hz
            rw [zipAddPad_length_local] at hl
            simp at hl
            omega
""",
"""          have htail : Galoistools.zipAddPad p xs ys ≠ [] := by
            intro hz
            have hl := congrArg List.length hz
            rw [zipAddPad_length_local] at hl
            have hle : xs.length ≤ ys.length := Nat.le_of_lt hlen
            have hm : Nat.max xs.length ys.length = ys.length := Nat.max_eq_right hle
            rw [hm] at hl
            simp at hl
            exact hys' hl
""")

src = src.replace(
"simp [last0, htail, ih ys hlen hys', Nat.mod_mod]",
"simp [last0, htail, hys', ih ys hlen hys']")
src = src.replace(
"simp [last0, hcv, cv, ih xs htail ys hys, Nat.mod_mod]",
"simp [last0, hcv, cv, htail, ih ys htail hys]")
src = src.replace(
"have iht := ih xs htail ys hys",
"have iht := ih ys htail hys")

src = src.replace(
"""theorem leadCoeff_reverse_eq_last0 (xs : List Nat) (hxs : xs ≠ []) :
    Galoistools.leadCoeff xs.reverse = last0 xs := by
  simpa using (last0_reverse xs.reverse)
""",
"""theorem leadCoeff_reverse_eq_last0 (xs : List Nat) (hxs : xs ≠ []) :
    Galoistools.leadCoeff xs.reverse = last0 xs := by
  simpa using (last0_reverse xs.reverse).symm
""")

old_reverse = """        | nil =>
            have := List.reverse_ne_nil.mpr htail
            contradiction
"""
new_reverse = """        | nil =>
            have hh := congrArg List.reverse hrev
            have hx : xs = [] := by simpa using hh
            exact (htail hx).elim
"""
assert old_reverse in src, 'reverse nonempty residual not found'
src = src.replace(old_reverse, new_reverse, 1)

old_hmul = """          simp [last0_reverse, Galoistools.leadCoeff] at hmul ⊢
          exact hmul
"""
new_hmul = """          rw [last0_reverse (a :: as), last0_reverse (b :: bs)]
          exact hmul
"""
assert old_hmul in src, 'terminal coefficient normalization residual not found'
src = src.replace(old_hmul, new_hmul, 1)

old_nonempty = """  intro hz
  have hrev := congrArg List.reverse hz
  simp at hrev
  have hfr : f.reverse ≠ [] := by simpa using hf
  have hgr : g.reverse ≠ [] := by simpa using hg
  have hlen := convolve_length_local p f.reverse g.reverse hfr hgr
  rw [hrev] at hlen
  simp at hlen
"""
new_nonempty = """  intro hz
  apply hlead
  simpa [hz, Galoistools.leadCoeff]
"""
assert old_nonempty in src, 'gfMul_nonempty residual not found'
src = src.replace(old_nonempty, new_nonempty, 1)

old_zero_iff = """  constructor
  · intro h
    by_contra hn
    push_neg at hn
    exact (gfMul_nonempty p f g hp hnf hng hn.1 hn.2) h
  · intro h
    simp [Galoistools.gfMul, h]
"""
new_zero_iff = """  constructor
  · intro h
    by_cases hf : f = []
    · exact Or.inl hf
    · by_cases hg : g = []
      · exact Or.inr hg
      · have hlead := reversed_convolve_lead_nonzero p f g hp hnf hng hf hg
        have hne : Galoistools.gfMul f g p ≠ [] := by
          simp only [Galoistools.gfMul, hf, hg, false_or, if_false]
          rw [gfStrip_self_of_leadCoeff_ne _ hlead]
          intro hz
          apply hlead
          simpa [hz, Galoistools.leadCoeff]
        exact (hne h).elim
  · intro h
    rcases h with hf | hg
    · subst f
      simp [Galoistools.gfMul]
    · subst g
      simp [Galoistools.gfMul]
"""
assert old_zero_iff in src, 'mul_zero_iff residual not found'
src = src.replace(old_zero_iff, new_zero_iff, 1)

exec(compile(src, '.github/scripts/vero_mul_leading_v3_generated.py', 'exec'), {'__name__': '__main__'})
