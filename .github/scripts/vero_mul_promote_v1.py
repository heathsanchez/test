from pathlib import Path

base = Path('../.github/scripts/vero_galoistools_allin.py').read_text()
marker = "patched = Path('allin_artifact.json').resolve()"
assert marker in base

injection = r'''
# Promote the fully verified multiplication leading-coefficient stack.
# Derive the auxiliary Lean block from the focused probe generator so the
# promoted benchmark proof is exactly the capability that was certified.
import ast
_mul_src = Path('../.github/scripts/vero_mul_leading_v1.py').read_text()
_mul_tree = ast.parse(_mul_src)
_shape = None
_leading = None
for _node in _mul_tree.body:
    if isinstance(_node, ast.Assign) and len(_node.targets) == 1 and isinstance(_node.targets[0], ast.Name):
        _name = _node.targets[0].id
        if _name == 'shape':
            _shape = ast.literal_eval(_node.value)
        elif _name == 'leading':
            assert _shape is not None
            assert isinstance(_node.value, ast.BinOp) and isinstance(_node.value.op, ast.Add)
            _leading = _shape + ast.literal_eval(_node.value.right)
assert _leading is not None
_mul_aux = _leading

_old = """          have htail : Galoistools.zipAddPad p xs ys ≠ [] := by
            intro hz
            have hl := congrArg List.length hz
            rw [zipAddPad_length_local] at hl
            simp at hl
            omega
"""
_new = """          have htail : Galoistools.zipAddPad p xs ys ≠ [] := by
            intro hz
            have hl := congrArg List.length hz
            rw [zipAddPad_length_local] at hl
            have hle : xs.length ≤ ys.length := Nat.le_of_lt hlen
            have hm : Nat.max xs.length ys.length = ys.length := Nat.max_eq_right hle
            rw [hm] at hl
            simp at hl
            exact hys' hl
"""
assert _old in _mul_aux
_mul_aux = _mul_aux.replace(_old, _new, 1)
_mul_aux = _mul_aux.replace(
    "simp [last0, htail, ih ys hlen hys', Nat.mod_mod]",
    "simp [last0, htail, hys', ih ys hlen hys']")
_mul_aux = _mul_aux.replace(
    "simp [last0, hcv, cv, ih xs htail ys hys, Nat.mod_mod]",
    "simp [last0, hcv, cv, htail, ih ys htail hys]")
_mul_aux = _mul_aux.replace(
    "have iht := ih xs htail ys hys",
    "have iht := ih ys htail hys")
_old = """        | nil =>
            have := List.reverse_ne_nil.mpr htail
            contradiction
"""
_new = """        | nil =>
            have hh := congrArg List.reverse hrev
            have hx : xs = [] := by simpa using hh
            exact (htail hx).elim
"""
assert _old in _mul_aux
_mul_aux = _mul_aux.replace(_old, _new, 1)
_old = """          simp [last0_reverse, Galoistools.leadCoeff] at hmul ⊢
          exact hmul
"""
_new = """          rw [last0_reverse (a :: as), last0_reverse (b :: bs)]
          exact hmul
"""
assert _old in _mul_aux
_mul_aux = _mul_aux.replace(_old, _new, 1)

set_slot('Galoistools/Proof/Ring.lean', 'proof_aux', 'prove_mul_degree_add', _mul_aux)
set_slot('Galoistools/Proof/Ring.lean', 'proof', 'prove_mul_degree_add', """  simp only [spec_mul_degree_add, canonical]
  intro f g p hp hnf hng hf hg
  simp only [Galoistools.gfMul, hf, hg, false_or, if_false]
  have hlead := reversed_convolve_lead_nonzero p f g hp hnf hng hf hg
  rw [gfStrip_self_of_leadCoeff_ne _ hlead]
  simp only [Galoistools.refGfDegree, List.length_reverse]
  have hfr : f.reverse ≠ [] := by simpa using hf
  have hgr : g.reverse ≠ [] := by simpa using hg
  rw [convolve_length_local p f.reverse g.reverse hfr hgr]
  simp only [List.length_reverse]
  have hfl : 0 < f.length := by cases f <;> simp_all
  have hgl : 0 < g.length := by cases g <;> simp_all
  omega""")

set_slot('Galoistools/Proof/Ring.lean', 'proof', 'prove_mul_zero_iff', """  simp only [spec_mul_zero_iff, canonical]
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
      simp [Galoistools.gfMul]""")

'''

promoted = base.replace(marker, injection + marker, 1)
exec(compile(promoted, '.github/scripts/vero_mul_promote_v1_generated.py', 'exec'), {'__name__': '__main__'})
