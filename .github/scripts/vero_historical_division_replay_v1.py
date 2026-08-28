from pathlib import Path
import re, subprocess, json, shutil

SRC = Path('coldcert/project').resolve()
OUT = Path('historical_division_replay_v1').resolve()
WORK = OUT/'work'
if WORK.exists(): shutil.rmtree(WORK)
OUT.mkdir(exist_ok=True)
shutil.copytree(SRC, WORK)

pf = WORK/'Galoistools/Proof/Division.lean'
src = pf.read_text()

def replace_proof(text, name, body):
    start = f'-- !benchmark @start proof def={name}'
    end = f'-- !benchmark @end proof def={name}'
    a = text.index(start) + len(start)
    b = text.index(end, a)
    return text[:a] + '\n' + body.rstrip() + '\n' + text[b:]

# Historical candidate: remainder idempotence via gfStrip idempotence.
rem_idem = r'''  intro f g p hp hg
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

# Historical candidate: division reconstruction for the current simple gfDiv shape.
div_identity = r'''  intro f g p hp hf hgNorm hlc
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

for name, body in [('prove_rem_idempotent', rem_idem), ('prove_div_identity', div_identity)]:
    if f'-- !benchmark @start proof def={name}' in src:
        src = replace_proof(src, name, body)
        print('REPLAYED', name)
    else:
        print('MISSING', name)
pf.write_text(src)

cp = subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=WORK,text=True,capture_output=True)
raw = cp.stdout+'\n'+cp.stderr
errs=[x for x in raw.splitlines() if 'error:' in x or 'error(' in x]
print('HISTORICAL_DIVISION_REPLAY_V1', json.dumps({'exit':cp.returncode,'error_lines':len(errs)}))
print(raw[-50000:])
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'error_lines':len(errs),'errors':errs},indent=2))
raise SystemExit(0)
