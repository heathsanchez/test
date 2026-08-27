from pathlib import Path
import json, subprocess, sys

# Reconstruct the certified 25/48 source first.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vero_galoistools_allin as base

out = Path('galoistools_allin/source').resolve()
impl = out / 'Galoistools/Impl/Division.lean'
proof = out / 'Galoistools/Proof/Division.lean'
orig_impl = impl.read_text()
orig_proof = proof.read_text()


def replace_code(text, name, body):
    start = f'-- !benchmark @start code def={name}'
    end = f'-- !benchmark @end code def={name}'
    a = text.index(start) + len(start)
    b = text.index(end, a)
    return text[:a] + '\n' + body.rstrip() + '\n' + text[b:]


def replace_proof(text, name, body):
    start = f'-- !benchmark @start proof def={name}'
    end = f'-- !benchmark @end proof def={name}'
    a = text.index(start) + len(start)
    b = text.index(end, a)
    return text[:a] + '\n' + body.rstrip() + '\n' + text[b:]

identity_body = r'''  intro f g p hp hf hgNorm hlc
  have hg0 : g ≠ [] := by
    intro h
    subst g
    simp [Galoistools.refLeadCoeff] at hlc
  have strip_bridge : ∀ xs : List Nat,
      Galoistools.gfStrip xs = Galoistools.refGfStrip xs := by
    intro xs
    induction xs with
    | nil => rfl
    | cons a as ih =>
        simp only [Galoistools.gfStrip, Galoistools.refGfStrip]
        by_cases h : a = 0
        · simp [h, ih]
        · simp [h]
  have ref_no_zero_head : ∀ xs ys : List Nat,
      Galoistools.refGfStrip xs ≠ 0 :: ys := by
    intro xs ys
    induction xs with
    | nil => simp [Galoistools.refGfStrip]
    | cons a as ih =>
        simp only [Galoistools.refGfStrip]
        by_cases h : a = 0
        · simp [h, ih]
        · simp [h]
  have hs : Galoistools.gfStrip f = f := by
    rw [strip_bridge]
    cases f with
    | nil => rfl
    | cons a as =>
        have ha : a ≠ 0 := by
          intro hzero
          subst a
          have h : Galoistools.refGfTrunc p (0 :: as) = 0 :: as := hf
          simp only [Galoistools.refGfTrunc, List.map_cons, Nat.zero_mod] at h
          exact ref_no_zero_head (0 :: as.map (fun x => x % p)) as h
        simp [Galoistools.refGfStrip, ha]
  have hadd : Galoistools.gfAdd [] f p = f := by
    have ht : Galoistools.gfTrunc p f = f := by
      rw [Galoistools.gfTrunc, strip_bridge]
      exact hf
    simpa [Galoistools.gfAdd, Galoistools.zipAddPad, Galoistools.gfTrunc] using ht
  simp only [canonical]
  rw [show Galoistools.gfDiv f g p = ([], Galoistools.gfStrip f) by
    simp [Galoistools.gfDiv, hg0]]
  simp [Galoistools.gfMul]
  rw [hs]
  exact hadd'''

rem_idem_body = r'''  intro f g p hp hg
  have hid : ∀ xs : List Nat,
      Galoistools.gfStrip (Galoistools.gfStrip xs) = Galoistools.gfStrip xs := by
    intro xs
    induction xs with
    | nil => rfl
    | cons a as ih =>
        simp only [Galoistools.gfStrip]
        by_cases ha : a = 0
        · simp [ha, ih]
        · simp [ha]
  simp [canonical, Galoistools.gfRem, Galoistools.gfDiv, hg, hid]'''

variants = {
  'preserve_empty_divisor_strip_remainder': '''  fun f g p =>
    if g = [] then ([], f)
    else ([], Galoistools.gfStrip f)''',
}

results=[]
for vname, gfbody in variants.items():
    print('DIV_VARIANT', vname)
    impl.write_text(replace_code(orig_impl, 'gfDiv', gfbody))
    ptxt = replace_proof(orig_proof, 'prove_div_identity', identity_body)
    ptxt = replace_proof(ptxt, 'prove_rem_idempotent', rem_idem_body)
    proof.write_text(ptxt)
    build = subprocess.run(['lake','build'], cwd=out, text=True, capture_output=True)
    raw = build.stdout + '\n' + build.stderr
    errors = [x for x in raw.splitlines() if 'error:' in x or 'error(' in x]
    # Count genuinely filled prove_ slots only if the full build certifies them.
    passed=[]
    if build.returncode == 0:
        for pf in [out/'Galoistools/Proof/Ring.lean', out/'Galoistools/Proof/Division.lean']:
            lines=pf.read_text().splitlines()
            for i,line in enumerate(lines):
                if line.startswith('theorem prove_'):
                    name=line.split()[1].split(':')[0]
                    j=i+1; body=[]
                    while j < len(lines) and not lines[j].startswith('-- !benchmark @end proof def=prove_'):
                        body.append(lines[j]); j += 1
                    if not any('sorry' in x for x in body): passed.append(name)
    item={
      'variant':vname,
      'lake_build_exit':build.returncode,
      'passed_count':len(passed),
      'passed':passed,
      'new_vs_25':[x for x in passed if x in ['prove_div_identity','prove_rem_idempotent']],
      'errors':errors[-12:],
      'raw_tail':'\n'.join(raw.splitlines()[-180:]) if build.returncode else ''
    }
    results.append(item)
    print('DIV_SEPARATOR_RESULT', json.dumps(item))

impl.write_text(orig_impl)
proof.write_text(orig_proof)
Path('galoistools_allin/div_boundary_separator.json').write_text(json.dumps(results,indent=2))
