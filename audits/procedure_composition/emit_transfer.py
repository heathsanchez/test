"""Replay immutable generated programs and compile their certificates to Lean.
No synthesis or source lower theorem is used to choose a certificate.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from fractions import Fraction as Q
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'cross_domain'))
sys.path.insert(0, str(ROOT.parent / 'procedure_repair'))
import checker
import composition
import emit as calculus

EXPECTED = {
    'programs.json': '738cb1ac37852cde8e4e04be14f91f0d4e779fa232cf0015297872bc300ed7b4',
    'certificates.json': '2518a941beb0f4092c7edc824e43cfd0a9860e63aab326f69973563f6a8eaea5',
}

def scalar(v):
    q = Q(v)
    return str(q.numerator) if q.denominator == 1 else f'({q.numerator} / {q.denominator} : ℝ)'

def poly(p, var='x'):
    return ' + '.join(f'({scalar(v)}) * {var} ^ {k}' for k, v in sorted(checker.norm(p).items())) or '(0 : ℝ)'

def ast_tree(t):
    if not isinstance(t, list) or not t: raise ValueError('invalid program tree')
    if len(t) == 1 and t[0] in ('constant','monomial','square','affine'): return (t[0],)
    if len(t) == 3 and t[0] in ('sum','product'): return (t[0], ast_tree(t[1]), ast_tree(t[2]))
    raise ValueError('invalid program tree')

def matches(t,c):
    if t[0] != c['kind']: return False
    return len(t) == 1 if len(t) == 1 else (len(c.get('children',[])) == 2 and all(matches(a,b) for a,b in zip(t[1:],c['children'])))

def program_expr(c):
    k=c['kind']; P='CrossDomainResidual.ProgramRules.Program'
    if k=='constant': return f'{P}.constant ({scalar(c["c"])})'
    if k=='monomial': return f'{P}.monomial ({scalar(c["c"])}) {int(c["power"])}'
    if k=='square': return f'{P}.square ({scalar(c["a"])}) ({scalar(c["b"])})'
    if k=='affine': return f'{P}.affine ({scalar(c["a"])}) ({scalar(c["b"])})'
    if k in ('sum','product'):
        a,b=c['children']
        return f'{P}.{k} ({program_expr(a)}) ({program_expr(b)})'
    raise ValueError(k)

def domain_expr(d):
    P='CrossDomainResidual.ProgramRules.Domain'
    return f'{P}.ray' if d[0]=='ray' else f'{P}.interval ({scalar(d[1])}) ({scalar(d[2])})'

def render_nonneg(name,p,d,c):
    expr=poly(p);dom=domain_expr(d)
    hypothesis='0 ≤ x' if d[0]=='ray' else f'{scalar(d[1])} ≤ x ∧ x ≤ {scalar(d[2])}'
    return f'''private def certificate : ProgramRules.Program := {program_expr(c)}
private theorem certificate_valid : ProgramRules.Valid ({dom}) certificate := by
  norm_num [certificate, ProgramRules.Valid, ProgramRules.NonnegativeDomain]
private theorem {name}_identity (x : ℝ) :
    {expr} = ProgramRules.eval certificate x := by
  simp [certificate, ProgramRules.eval]
  ring

theorem {name} {{x : ℝ}} (hx : {hypothesis}) :
    0 ≤ {expr} := by
  rw [{name}_identity]
  exact ProgramRules.sound certificate ({dom}) x certificate_valid hx
'''

def render_lower(p,d,c):
    # Reuse only the previously checked calculus template. The dummy certificate
    # supplies no mathematics to the emitted proof; its nonnegativity block is discarded.
    template=calculus.render_lower(p,d,{'kind':'square','power':1,'A':'1/2','r':'1','D':'0'})
    tail=template.split('private theorem derivative_certificate',1)[1].split('#print axioms derivative_nonneg',1)[0]
    return '''import Mathlib
import ProgramRules
noncomputable section
namespace CrossDomainResidual.ProcedureRepair
open Real Set

''' + render_nonneg('derivative_nonneg',p,d,c) + '\nprivate theorem derivative_certificate' + tail + '''#print axioms derivative_nonneg
#print axioms recovered_lower
end CrossDomainResidual.ProcedureRepair
'''

def render_interval(p,d,c):
    return '''import Mathlib
import ProgramRules
namespace CrossDomainResidual.ProcedureRepair
''' + render_nonneg('interval_nonneg',p,d,c) + '''#print axioms interval_nonneg
end CrossDomainResidual.ProcedureRepair
'''

def emit(source,out):
    source=Path(source);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for name,digest in EXPECTED.items():
        assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest, name
    trees=[ast_tree(t) for t in json.loads((source/'programs.json').read_text())]
    certs=json.loads((source/'certificates.json').read_text())
    assert len(trees)==len(certs)==2
    records=[]
    for i,((p,d),t,c) in enumerate(zip(composition.stages(),trees,certs)):
        assert matches(t,c) and checker.verify(c,p,d)
        meter=composition.Meter()
        assert composition.Program(t)(p,d,meter)==c
        reuse=[]
        for hp,hd in composition.heldouts(i):
            h=composition.Program(t)(hp,hd,meter)
            assert h is not None and checker.verify(h,hp,hd)
            reuse.append({'polynomial':composition.encode(hp),'domain':list(map(str,hd)),'certificate':h})
        records.append({'program':t,'polynomial':composition.encode(p),'domain':list(map(str,d)),'certificate':c,'reuse':reuse})
    assert trees[0]!=trees[1]
    (out/'RecoveredProcedures.lean').write_text(render_lower(*composition.stages()[0],certs[0]))
    (out/'HeldoutProcedure.lean').write_text(render_interval(*composition.stages()[1],certs[1]))
    (out/'certificate.json').write_text(json.dumps(records,indent=2)+'\n')
    import subprocess
    names=['RecoveredProcedures.lean','HeldoutProcedure.lean']
    with (out/'source.sha256').open('w') as f:
        for name in names:f.write(hashlib.sha256((out/name).read_bytes()).hexdigest()+'  '+name+'\n')
    for name in names:
        text=(out/name).read_text()
        assert 'import ABAngleBounds' not in text and 'self_sub_cube_le_arctan' not in text
        assert '\nsorry' not in text and '\nadmit' not in text
    print('COMPOSITION_TRANSFER_EMITTED',json.dumps({'programs':trees,'replay':'PASS','reuse':'PASS'}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args();emit(a.source,a.out)
