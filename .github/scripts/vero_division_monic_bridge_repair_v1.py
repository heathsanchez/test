from pathlib import Path
import json, shutil, subprocess

BASE = Path('baseline28/galoistools_allin28').resolve()
OUT = Path('division_monic_bridge_repair_v1').resolve()
WORK = OUT / 'work'
OUT.mkdir(exist_ok=True)
if WORK.exists(): shutil.rmtree(WORK)
shutil.copytree(BASE, WORK)

ring = WORK/'Galoistools/Proof/Ring.lean'
div = WORK/'Galoistools/Proof/Division.lean'
src = div.read_text()

old = '''        have hdle : d ≤ a := Nat.le_of_dvd (Nat.pos_of_ne_zero ha0) hda
        have hdlt : d < p := lt_of_le_of_lt hdle hlt
        have hd0 : d ≠ 0 := by
          intro hd
          subst d
          simp at hdp
          omega
        by_cases hd1 : d = 1
'''
new = '''        have hdle : d ≤ a := Nat.le_of_dvd (Nat.pos_of_ne_zero ha0) hda
        have hdlt : d < p := Nat.lt_of_le_of_lt hdle hlt
        have hd0 : d ≠ 0 := by
          intro hd
          subst d
          simp at hda
          exact ha0 hda
        by_cases hd1 : d = 1
'''
if old not in src:
    raise RuntimeError('expected gcd block not found')
src = src.replace(old,new,1)

# Keep the existing local monic_norm shape, but remove the inaccessible Ring theorem dependency.
old2 = '''  have monic_norm : ∀ xs : List Nat,
      Galoistools.IsNorm p xs → xs ≠ [] →
      Galoistools.refLeadCoeff (Galoistools.gfMonic xs p).2 = 1 := by
    intro xs hn hne
    exact prove_monic_leadCoeff_one xs p hp1 hne (norm_lead_coprime xs hn hne)
'''
new2 = '''  have monic_norm : ∀ xs : List Nat,
      Galoistools.IsNorm p xs → xs ≠ [] →
      Galoistools.refLeadCoeff (Galoistools.gfMonic xs p).2 = 1 := by
    intro xs hn hne
    cases xs with
    | nil => contradiction
    | cons a as =>
      simp only [Galoistools.gfMonic]
      by_cases ha1 : a = 1
      · simp [ha1, Galoistools.refLeadCoeff]
      · have hc : Nat.gcd a p = 1 := by
          simpa [Galoistools.refLeadCoeff] using norm_lead_coprime (a::as) hn (by simp)
        simp [ha1, Galoistools.refLeadCoeff, Galoistools.gfQuoGround, hc]
'''
if old2 not in src:
    raise RuntimeError('expected monic_norm block not found')
src = src.replace(old2,new2,1)
div.write_text(src)

def run(args):
    cp=subprocess.run(args,cwd=WORK,text=True,capture_output=True)
    raw=cp.stdout+'\n'+cp.stderr
    return {'exit':cp.returncode,'tail':raw[-40000:]}

r_ring=run(['lake','build','Galoistools.Proof.Ring'])
r_div=run(['lake','build','Galoistools.Proof.Division'])
res={'ring':r_ring,'division':r_div}
(OUT/'result.json').write_text(json.dumps(res,indent=2))
print('DIVISION_MONIC_BRIDGE_REPAIR_V1', json.dumps({'ring_exit':r_ring['exit'],'division_exit':r_div['exit']}))
if r_div['exit']:
    print('DIVISION_RESIDUAL\n'+r_div['tail'])
raise SystemExit(0 if r_ring['exit']==0 and r_div['exit']==0 else 1)
