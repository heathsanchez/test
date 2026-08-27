from pathlib import Path

src = Path('../.github/scripts/vero_allin_mul26.py').read_text()
marker = "\n'''\n\nbase = base.replace(needle, injection"
assert marker in src

addition = r'''
set_slot('Galoistools/Proof/Ring.lean','proof_aux','prove_mul_zero_iff', _mul_aux)
set_slot('Galoistools/Proof/Ring.lean','proof','prove_mul_zero_iff', '''  simp only [spec_mul_zero_iff, canonical]
  intro f g p hp hnf hng
  constructor
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
      simp [Galoistools.gfMul]''')
'''

src = src.replace(marker, '\n' + addition + marker, 1)
exec(compile(src, '.github/scripts/vero_allin_mul27_generated.py', 'exec'), {'__name__':'__main__'})
