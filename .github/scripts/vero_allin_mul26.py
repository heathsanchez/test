from pathlib import Path

base = Path('../.github/scripts/vero_galoistools_allin.py').read_text()
needle = "patched = Path('allin_artifact.json').resolve()"
assert needle in base

injection = r'''
# Promote the independently verified multiplication degree capability.
# Reconstruct the exact green helper layer from the focused V1 source, applying
# the corrections certified by multiplication-leading V3 run 4.
import ast
_mul_py = Path('../.github/scripts/vero_mul_leading_v1.py').read_text()
_tree = ast.parse(_mul_py)
_shape = None
_lead_suffix = None
for _node in _tree.body:
    if isinstance(_node, ast.Assign) and len(_node.targets) == 1 and isinstance(_node.targets[0], ast.Name):
        _nm = _node.targets[0].id
        if _nm == 'shape' and isinstance(_node.value, ast.Constant):
            _shape = _node.value.value
        elif _nm == 'leading' and isinstance(_node.value, ast.BinOp) and isinstance(_node.value.right, ast.Constant):
            _lead_suffix = _node.value.right.value
assert _shape is not None and _lead_suffix is not None
_mul_aux = _shape + _lead_suffix

_mul_aux = _mul_aux.replace(
'''          have htail : Galoistools.zipAddPad p xs ys ≠ [] := by
            intro hz
            have hl := congrArg List.length hz
            rw [zipAddPad_length_local] at hl
            simp at hl
            omega
''',
'''          have htail : Galoistools.zipAddPad p xs ys ≠ [] := by
            intro hz
            have hl := congrArg List.length hz
            rw [zipAddPad_length_local] at hl
            have hle : xs.length ≤ ys.length := Nat.le_of_lt hlen
            have hm : Nat.max xs.length ys.length = ys.length := Nat.max_eq_right hle
            rw [hm] at hl
            simp at hl
            exact hys' hl
''')
_mul_aux = _mul_aux.replace(
    "simp [last0, htail, ih ys hlen hys', Nat.mod_mod]",
    "simp [last0, htail, hys', ih ys hlen hys']")
_mul_aux = _mul_aux.replace(
    "simp [last0, hcv, cv, ih xs htail ys hys, Nat.mod_mod]",
    "simp [last0, hcv, cv, htail, ih ys htail hys]")
_mul_aux = _mul_aux.replace(
    "have iht := ih xs htail ys hys",
    "have iht := ih ys htail hys")
_mul_aux = _mul_aux.replace(
'''        | nil =>
            have := List.reverse_ne_nil.mpr htail
            contradiction
''',
'''        | nil =>
            have hh := congrArg List.reverse hrev
            have hx : xs = [] := by simpa using hh
            exact (htail hx).elim
''')
_mul_aux = _mul_aux.replace(
'''          simp [last0_reverse, Galoistools.leadCoeff] at hmul ⊢
          exact hmul
''',
'''          rw [last0_reverse (a :: as), last0_reverse (b :: bs)]
          exact hmul
''')

set_slot('Galoistools/Proof/Ring.lean','proof_aux','prove_mul_degree_add', _mul_aux)
set_slot('Galoistools/Proof/Ring.lean','proof','prove_mul_degree_add', '''  simp only [spec_mul_degree_add, canonical]
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
  omega''')
'''

base = base.replace(needle, injection + "\n" + needle, 1)
exec(compile(base, '.github/scripts/vero_allin_mul26_generated.py', 'exec'), {'__name__':'__main__'})
