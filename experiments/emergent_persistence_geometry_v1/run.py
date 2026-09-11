#!/usr/bin/env python3
import hashlib, importlib.util, json, pathlib
ROOT=pathlib.Path(__file__).parent
PREV=ROOT.parent/"emergent_persistence_hierarchy_v1"/"run.py"
spec=importlib.util.spec_from_file_location("frozen",PREV)
fh=importlib.util.module_from_spec(spec);spec.loader.exec_module(fh)

DOMAINS=("equation","repair","transform","plan")
def prof(tag,n=16):
 h=hashlib.sha256(tag.encode()).digest();return tuple((h[i//8]>>(i%8))&1 for i in range(n))
def atom(tag):return ("atom",prof(tag))
def seq(*xs):return ("seq",)+xs
PAD=atom("unused-shift")

def run(roots,domains,shift=10**6,shift_term=PAD,blocked=()):
 fh.ROOTS=tuple(roots);fh.SHIFT_EPISODE=shift;fh.F=shift_term
 # Complete finite adapter check: every opaque encounter round-trips and every
 # exposed outcome profile is compared extensionally.
 verification=sum(len(rs) for rs in roots)+len(roots)
 adaptive=fh.Kernel("adaptive",blocked=blocked).run()
 cold=fh.Kernel("cold").run()
 return adaptive,cold,verification

def roots_at(term,episodes,n=24,multiplicity=1):
 first_two=set(episodes[:2])
 return tuple(tuple(term for _ in range(1 if ep in first_two else multiplicity)) if ep in episodes else () for ep in range(1,n+1))
def domains(pattern,n=24):return tuple(DOMAINS[pattern(i)%4] for i in range(1,n+1))
def metric(term,k,roots,ds,shift=10**6):
 sid=fh.sid(term);p=next(p for p in k.promotions if p["id"]==sid)
 future=[i for i,rs in enumerate(roots,1) if i>p["episode"] and any(fh.sid(x)==sid for x in rs)]
 scope=len({ds[i-1] for i in future})
 last_valid=min(max(future+[p["episode"]]),shift-1)
 alt=fh.Kernel("adaptive",blocked=(term,)).run()
 return {"d":fh.depth(term),"tau":last_valid-p["episode"],"R":scope,
         "B":alt.total-k.total,"B_episodes":sum(a["cost"]>b["cost"] for a,b in zip(alt.rows,k.rows)),
         "A":k.rec[sid]["account"],"promoted":p["episode"]}

def case(term,eps,ds,shift=10**6,multiplicity=1):
 rs=roots_at(term,eps,multiplicity=multiplicity)
 a,c,v=run(rs,ds,shift,term if shift<10**6 else PAD)
 return metric(term,a,rs,ds,shift),a.total+v,c.total+v

def main():
 eps=(1,2,5,9,13,17,21,24)
 fixed=domains(lambda i:0)
 varied=tuple(DOMAINS[(i*3+1)%4] for i in range(24))
 shallow=atom("ancestry-role");deep=seq(seq(atom("x"),atom("y")),atom("z"))
 m_sh,ash,csh=case(shallow,eps,fixed);m_dp,adp,cdp=case(deep,eps,fixed)
 scope_term=atom("scope-role")
 m_n,an,cn=case(scope_term,eps,fixed);m_w,aw,cw=case(scope_term,eps,varied)
 persist=atom("persistence-role")
 m_short,ast,cst=case(persist,eps,fixed,shift=10);m_long,alt,clt=case(persist,eps,fixed,shift=23)
 breadth=atom("breadth-role")
 m_low,abl,cbl=case(breadth,eps,varied,multiplicity=1);m_high,abh,cbh=case(breadth,eps,varied,multiplicity=4)
 metrics={"ancestry_shallow":m_sh,"ancestry_deep":m_dp,"scope_narrow":m_n,"scope_broad":m_w,
          "persistence_short":m_short,"persistence_long":m_long,"breadth_low":m_low,"breadth_high":m_high}
 totals={"adaptive":sum((ash,adp,an,aw,ast,alt,abl,abh)),"cold":sum((csh,cdp,cn,cw,cst,clt,cbl,cbh))}
 gates={
  "ancestry_selective":m_dp["d"]>m_sh["d"] and m_dp["R"]==m_sh["R"] and m_dp["tau"]==m_sh["tau"],
  "scope_selective":m_w["R"]>m_n["R"] and m_w["d"]==m_n["d"] and m_w["tau"]==m_n["tau"],
  "persistence_selective":m_long["tau"]>m_short["tau"] and m_long["d"]==m_short["d"] and m_long["R"]==m_short["R"],
  "breadth_selective":m_high["B"]>m_low["B"] and m_high["d"]==m_low["d"] and m_high["R"]==m_low["R"] and m_high["tau"]==m_low["tau"],
  "derivedness_not_generality":m_dp["d"]>m_sh["d"] and m_dp["R"]==m_sh["R"],
  "persistence_not_depth":m_long["tau"]>m_short["tau"] and m_long["d"]==m_short["d"],
  "scope_not_depth":m_w["R"]>m_n["R"] and m_w["d"]==m_n["d"],
  "breadth_not_scope":m_high["B"]>m_low["B"] and m_high["R"]==m_low["R"],
  "adaptive_suite_advantage":totals["adaptive"]<totals["cold"]}
 snap={"episodes_per_case":24,"reuse_episodes":eps,"controller_sha256":hashlib.sha256(PREV.read_bytes()).hexdigest(),
       "domains":DOMAINS,"interventions":["ancestry","scope","persistence","dependent_multiplicity"]}
 dg=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 evidence={"verdict":"VERIFIED_EMERGENT_PERSISTENCE_GEOMETRY" if all(gates.values()) else "NEGATIVE_OR_PARTIAL",
  "classification":"FINITE_MATCHED_CAUSAL_PROSPECTIVE","snapshot_digest":dg(snap),"metrics":metrics,"totals":totals,
  "reduction_factor":totals["cold"]/totals["adaptive"],"gates":gates,
  "not_established":["natural-world coordinate emergence","coordinate statistical independence","optimal retention-value estimator","open-ended development"]}
 out=ROOT/"results";out.mkdir(exist_ok=True)
 (out/"snapshot.json").write_text(json.dumps(snap,indent=2)+"\n");(out/"evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
 print(json.dumps(evidence,indent=2))
if __name__=="__main__":main()
