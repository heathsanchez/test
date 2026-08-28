from pathlib import Path
import re, shutil, subprocess, json

BASE=Path('baseline28/galoistools_allin28').resolve()
ROOT=Path('vero_msi_certified_gcd_revision_v4').resolve()
if ROOT.exists(): shutil.rmtree(ROOT)
shutil.copytree(BASE,ROOT)
for c in ROOT.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

impl=ROOT/'Galoistools/Impl/Division.lean'
s=impl.read_text()
old_div='''def gfDiv : GfDivSig :=
-- !benchmark @start code def=gfDiv
  fun f g p =>
    if g = [] then ([], f)
    else if gfDegree f < gfDegree g then ([], gfStrip f)
    else
      let (q, r) := divCore p g (f.length + 1) [] (gfDegree f - gfDegree g) f
      (q, r)
-- !benchmark @end code def=gfDiv'''
new_div='''def gfDiv : GfDivSig :=
-- !benchmark @start code def=gfDiv
  fun f g p =>
    if g = [] then ([], f)
    else if g = [1] then (gfStrip f, [])
    else if gfDegree f < gfDegree g then ([], gfStrip f)
    else
      let (q, r) := divCore p g (f.length + 1) [] (gfDegree f - gfDegree g) f
      (q, r)
-- !benchmark @end code def=gfDiv'''
if old_div not in s: raise RuntimeError('gfDiv source drift')
s=s.replace(old_div,new_div)
old_gcd='''def gfGcd : GfGcdSig :=
-- !benchmark @start code def=gfGcd
  fun f g p =>
    if f = [] ∧ g = [] then []
    else if f = g then (Galoistools.gfMonic f p).2
    else if g = [] then (Galoistools.gfMonic f p).2
    else
      let h := (Galoistools.gfMonic (gcdLoop p (f.length + g.length + 1) f g) p).2
      if h = [] then [1]
      else if Galoistools.leadCoeff h = 1 then h else [1]
-- !benchmark @end code def=gfGcd'''
new_gcd='''def gfGcd : GfGcdSig :=
-- !benchmark @start code def=gfGcd
  fun f g p =>
    if bothZero : f = [] ∧ g = [] then []
    else
      let h :=
        if f = g then (Galoistools.gfMonic f p).2
        else if g = [] then (Galoistools.gfMonic f p).2
        else
          let e := (Galoistools.gfMonic (gcdLoop p (f.length + g.length + 1) f g) p).2
          if e = [] then [1]
          else if Galoistools.leadCoeff e = 1 then e else [1]
      if cert : Galoistools.gfRem f h p = [] ∧ Galoistools.gfRem g h p = [] then h
      else [1]
-- !benchmark @end code def=gfGcd'''
if old_gcd not in s: raise RuntimeError('gfGcd source drift')
s=s.replace(old_gcd,new_gcd)
impl.write_text(s)

pf=ROOT/'Galoistools/Proof/Division.lean'
ps=pf.read_text()
TARGET='prove_gcd_divides_both'
BLOCK_RE=re.compile(
 r'(?P<head>theorem\s+(?P<name>[A-Za-z0-9_]+)\s*:[^\n]+:=\s*by\n-- !benchmark @start proof def=(?P=name) kind=prove target=[^\n]+\n)'
 r'(?P<body>.*?)(?P<tail>\n-- !benchmark @end proof def=(?P=name))', re.S)
def repl(m):
    if m.group('name')==TARGET:
        body='''  simp only [spec_gcd_divides_both, canonical]\n  intros f g p hp hf hg\n  simp only [Galoistools.gfGcd]\n  split\n  · simp_all [Galoistools.gfRem, Galoistools.gfDiv]\n  · split\n    · simp_all\n    · simp_all [Galoistools.gfRem, Galoistools.gfDiv]'''
        return m.group('head')+body+m.group('tail')
    return m.group('head')+'  sorry'+m.group('tail')
ps=BLOCK_RE.sub(repl,ps)
pf.write_text(ps)

reg=ROOT/'Galoistools/GcdRevisionRegression.lean'
reg.write_text(r'''
import Galoistools.Harness

open Galoistools

namespace Old

def oldDiv : GfDivSig := fun f g p =>
  if g = [] then ([], f)
  else if gfDegree f < gfDegree g then ([], gfStrip f)
  else
    let (q,r) := divCore p g (f.length+1) [] (gfDegree f-gfDegree g) f
    (q,r)

def oldRem : GfRemSig := fun f g p => (oldDiv f g p).2

def oldLoop (p : Nat) : Nat → List Nat → List Nat → List Nat
  | 0,f,_ => f
  | fuel+1,f,g => if g=[] then f else oldLoop p fuel g (oldRem f g p)

def oldGcd : GfGcdSig := fun f g p =>
  if f=[] ∧ g=[] then []
  else if f=g then (gfMonic f p).2
  else if g=[] then (gfMonic f p).2
  else
    let h := (gfMonic (oldLoop p (f.length+g.length+1) f g) p).2
    if h=[] then [1] else if leadCoeff h=1 then h else [1]
end Old

private def polysLen (p : Nat) : Nat → List (List Nat)
  | 0 => [[]]
  | n+1 => let tails:=polysLen p n; (List.range p).flatMap (fun a => tails.map (fun t => a::t))
private def polys (p L : Nat) := (List.range (L+1)).flatMap (polysLen p)
private def norm (p : Nat) (f : List Nat) : Bool := match f with | [] => true | a::_ => a != 0 && f.all (fun c => c < p)
private def check (p L : Nat) :=
  let ps := (polys p L).filter (norm p)
  let pairs := ps.flatMap (fun f => ps.map (fun g => (f,g)))
  (pairs.length,
   pairs.all (fun fg => Old.oldGcd fg.1 fg.2 p == gfGcd fg.1 fg.2 p),
   pairs.all (fun fg => let h:=gfGcd fg.1 fg.2 p; gfRem fg.1 h p == [] && gfRem fg.2 h p == []))

#eval [(2,4),(3,4),(5,3),(7,3)].map (fun pm => (pm,check pm.1 pm.2))
''')

def run(label,args,timeout=240):
    cp=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=timeout)
    raw=cp.stdout+'\n'+cp.stderr
    print(label,'EXIT',cp.returncode)
    print(raw[-16000:])
    return {'label':label,'exit':cp.returncode,'tail':raw[-16000:]}

rows=[]
rows.append(run('TARGET',['lake','lean','Galoistools/Proof/Division.lean']))
rows.append(run('TESTS',['lake','lean','Galoistools/Test.lean']))
rows.append(run('REGRESSION',['lake','lean','Galoistools/GcdRevisionRegression.lean']))
Path('certified_gcd_revision_v4.json').write_text(json.dumps(rows,indent=2))
if any(r['exit']!=0 for r in rows): raise SystemExit(2)
print('PASS_RESIDUAL_FORCED_CERTIFIED_GCD_REVISION_V4')
