from pathlib import Path
import shutil, subprocess

BASE=Path('baseline28/galoistools_allin28').resolve()
OUT=Path('vero_msi_gcd_truth_census_v3').resolve()
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for c in OUT.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=OUT/'Galoistools/GcdTruthCensus.lean'
probe.write_text(r'''
import Galoistools.Harness

open Galoistools

private def polysLen (p : Nat) : Nat → List (List Nat)
  | 0 => [[]]
  | n+1 =>
      let tails := polysLen p n
      (List.range p).flatMap (fun a => tails.map (fun t => a :: t))

private def allPolys (p maxLen : Nat) : List (List Nat) :=
  (List.range (maxLen+1)).flatMap (polysLen p)

private def norm (p : Nat) (f : List Nat) : Bool :=
  match f with
  | [] => true
  | a::_ => a != 0 && f.all (fun c => c < p)

private def oneP (p maxLen : Nat) : Nat × Nat × Option (List Nat × List Nat × List Nat × List Nat × List Nat) :=
  let ps := (allPolys p maxLen).filter (norm p)
  let pairs := ps.flatMap (fun f => ps.map (fun g => (f,g)))
  let bad := pairs.find? (fun fg =>
    let f:=fg.1; let g:=fg.2
    let h := gfGcd f g p
    gfRem f h p != [] || gfRem g h p != [])
  match bad with
  | none => (ps.length, pairs.length, none)
  | some (f,g) =>
      let h:=gfGcd f g p
      (ps.length,pairs.length,some (f,g,h,gfRem f h p,gfRem g h p))

#eval [(2, 4), (3, 4), (5, 4), (7, 3)].map (fun pm => (pm, oneP pm.1 pm.2))
''')
cp=subprocess.run(['lake','lean','Galoistools/GcdTruthCensus.lean'],cwd=OUT,text=True,capture_output=True,timeout=240)
raw=cp.stdout+'\n'+cp.stderr
Path('gcd_truth_census_v3.txt').write_text(raw)
print('GCD_TRUTH_CENSUS_V3_EXIT',cp.returncode)
print(raw[-20000:])
raise SystemExit(cp.returncode)
