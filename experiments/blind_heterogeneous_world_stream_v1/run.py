#!/usr/bin/env python3
import hashlib, importlib.util, json, pathlib

ROOT = pathlib.Path(__file__).parent
PREV = ROOT.parent / "emergent_persistence_hierarchy_v1" / "run.py"
spec = importlib.util.spec_from_file_location("frozen_hierarchy", PREV)
fh = importlib.util.module_from_spec(spec); spec.loader.exec_module(fh)

# Four disjoint finite surface languages. Domain metadata never enters Kernel.
CODECS = {
 "equational": ("lhs", "rhs", "rewrite"),
 "repair": ("bug", "patch", "test"),
 "transform": ("grid", "tile", "map"),
 "planning": ("state", "move", "goal"),
}

def profile(tag, n=12):
    h=hashlib.sha256(tag.encode()).digest()
    return tuple((h[i//8]>>(i%8))&1 for i in range(n))
def atom(tag): return ("atom", profile(tag))
def seq(*xs): return ("seq",)+xs

A,B,C = map(atom,("shared/a","shared/b","shared/c"))
F,F2 = atom("family/pre"),atom("family/post")
D=seq(A,B); E=seq(D,C)
locals_={d:atom("local/"+d) for d in CODECS}

# Same recurrence logic as the predecessor, extended prospectively across four
# distinct encodings. One-off terms have no repeated verified identity.
BASE=(
 (F,A), (A,B), (F,A,B), (A,B,C), (F,D), (A,B,C),
 (F,D,C), (D,C), (F,D), (D,C), (F,D,C), (E,),
 (F2,E), (E,), (F2,D,E), (E,), (F2,D,E), (E,),
 (F2,D,E), (E,), (D,E), (E,), (D,E), (E,),
 (F2,D,E), (E,), (D,E), (E,), (F2,D,E), (E,), (D,E), (E,)
)
DOMAINS=tuple(CODECS)[0],tuple(CODECS)[1],tuple(CODECS)[2],tuple(CODECS)[3]
DOMAIN_SCHEDULE=tuple(DOMAINS[i%4] for i in range(len(BASE)))
ROOTS=tuple(rs+((locals_[DOMAIN_SCHEDULE[i]],) if i in (0,7,18,29) else ()) for i,rs in enumerate(BASE))

def surface_encode(domain, episode, roots):
    words=CODECS[domain]
    raw=json.dumps(roots,separators=(",",":"))
    key=(episode*17+len(domain))%251
    payload=bytes((b^key) for b in raw.encode()).hex()
    return {"carrier":words[0],"operator":words[1],"authority":words[2],"nonce":episode,"payload":payload}
def surface_decode(domain, obj):
    assert tuple(obj[k] for k in ("carrier","operator","authority"))==CODECS[domain]
    key=(obj["nonce"]*17+len(domain))%251
    raw=bytes((b^key) for b in bytes.fromhex(obj["payload"])).decode()
    def tup(x): return tuple(tup(y) if isinstance(y,list) else y for y in x)
    return tup(json.loads(raw))
def verify_adapters(roots=ROOTS):
    calls=0; digests=[]
    for ep,(domain,rs) in enumerate(zip(DOMAIN_SCHEDULE,roots),1):
        opaque=surface_encode(domain,ep,rs); recovered=surface_decode(domain,opaque)
        assert recovered==rs
        # Complete authority-profile equality, not token agreement.
        for a,b in zip(recovered,rs): assert fh.canon(a)==fh.canon(b); calls+=1
        digests.append(hashlib.sha256(json.dumps(opaque,sort_keys=True).encode()).hexdigest())
    return calls,digests

def configure(roots):
    fh.ROOTS=roots; fh.SHIFT_EPISODE=13; fh.F=F; fh.F2=F2; fh.D=D; fh.E=E
def run_mode(mode="adaptive",blocked=()):
    return fh.Kernel(mode,blocked=blocked).run()
def occurrences(term, start):
    k=fh.sid(term); eps=[]; ds=set()
    for ep,(domain,rs) in enumerate(zip(DOMAIN_SCHEDULE,ROOTS),1):
        if ep<=start: continue
        if any(k in {fh.sid(t) for t in fh.subterms(r)} for r in rs): eps.append(ep);ds.add(domain)
    return len(eps),len(ds)
def breadth(term, adaptive):
    alt=fh.Kernel("adaptive",blocked=(term,)).run()
    return sum(x["cost"]>y["cost"] for x,y in zip(alt.rows,adaptive.rows))

def scrambled():
    # Preserve every AST shape but salt every atom profile by encounter.
    def salt(x,ep,path="r"):
        if x[0]=="atom": return ("atom",profile(f"scramble/{ep}/{path}"))
        return ("seq",)+tuple(salt(y,ep,f"{path}.{i}") for i,y in enumerate(x[1:]))
    return tuple(tuple(salt(r,ep,str(i)) for i,r in enumerate(rs)) for ep,rs in enumerate(ROOTS,1))

def dg(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def main():
    configure(ROOTS); adapter_calls,surface_digests=verify_adapters()
    adaptive=run_mode(); cold=run_mode("cold"); sham=run_mode("sham"); memory=run_mode("answer_memory")
    no_deep=run_mode(blocked=(D,)); no_shallow=run_mode(blocked=(F,))
    radii=[]
    for p in adaptive.promotions:
        term=adaptive.rec[p["id"]]["term"]; future,domains=occurrences(term,p["episode"])
        radii.append({"id":p["id"],"depth":p["depth"],"promoted":p["episode"],"future_episodes":future,"future_domains":domains,"ablation_breadth":breadth(term,adaptive)})
    by_depth={}
    for r in radii:
        z=by_depth.setdefault(str(r["depth"]),[]);z.append(r)
    summary={d:{k:sum(r[k] for r in xs)/len(xs) for k in ("future_episodes","future_domains","ablation_breadth")} for d,xs in by_depth.items()}
    depths=sorted(map(int,summary)); keys=("future_episodes","future_domains","ablation_breadth")
    monotone=all(all(summary[str(a)][k]<=summary[str(b)][k] for a,b in zip(depths,depths[1:])) for k in keys)
    strict=all(summary[str(depths[0])][k]<summary[str(depths[-1])][k] for k in keys)
    normal_totals={k:v.total+adapter_calls for k,v in {"cold":cold,"adaptive":adaptive,"deep_ablation":no_deep,"shallow_ablation":no_shallow,"sham":sham,"answer_memory":memory}.items()}
    scr=scrambled(); configure(scr); scr_calls,_=verify_adapters(scr); scr_adapt=run_mode(); scr_cold=run_mode("cold")
    scramble_totals={"cold":scr_cold.total+scr_calls,"adaptive":scr_adapt.total+scr_calls}
    configure(ROOTS)
    gates={
      "all_adapters_exhaustively_verified":adapter_calls==sum(len(x) for x in ROOTS),
      "heterogeneous_domains":len(set(DOMAIN_SCHEDULE))==4,
      "adaptive_beats_cold":normal_totals["adaptive"]<normal_totals["cold"],
      "depth_predicts_reuse_radius":monotone and strict,
      "recursive_depth_emerges":max(depths)>=2,
      "deep_ablation_broader_than_shallow":sum(a["cost"]>b["cost"] for a,b in zip(no_deep.rows,adaptive.rows))>sum(a["cost"]>b["cost"] for a,b in zip(no_shallow.rows,adaptive.rows)),
      "scramble_destroys_hierarchy":len({p["depth"] for p in scr_adapt.promotions})<len(depths),
      "scramble_has_no_adaptive_gain":scramble_totals["adaptive"]>=scramble_totals["cold"],
      "sham_not_help":normal_totals["sham"]>=normal_totals["cold"],
      "answer_memory_not_help":normal_totals["answer_memory"]>=normal_totals["cold"]}
    snapshot={"episodes":len(ROOTS),"domains":list(DOMAIN_SCHEDULE),"surface_digests":surface_digests,"adapter_calls":adapter_calls,"base_stream_digest":dg(ROOTS),"scramble_digest":dg(scr),"controller_sha256":hashlib.sha256(PREV.read_bytes()).hexdigest(),"primary_gate":"depth predicts prospective future-episode, future-domain, and ablation radius"}
    evidence={"verdict":"VERIFIED_BLIND_HETEROGENEOUS_HIERARCHY" if all(gates.values()) else "NEGATIVE_OR_PARTIAL","classification":"FINITE_CONSTRUCTED_VERIFIER_BACKED_PROSPECTIVE","snapshot_digest":dg(snapshot),"totals":normal_totals,"reduction_factor":normal_totals["cold"]/normal_totals["adaptive"],"reuse_radius":radii,"by_depth":summary,"scramble":scramble_totals,"promotions":adaptive.promotions,"revocations":adaptive.revocations,"gates":gates,"not_established":["natural-world ecological validity","open-ended domain discovery","unbounded recursive development","optimality of learned depth"]}
    out=ROOT/"results";out.mkdir(exist_ok=True)
    (out/"snapshot.json").write_text(json.dumps(snapshot,indent=2)+"\n")
    (out/"evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))
if __name__=="__main__": main()
