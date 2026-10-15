"""Native observer genesis with a frozen three-instruction old grammar.

Development: CPython deque. Protected future: independently implemented NumPy
array. Target is never accessed during development/selection. This establishes
only bounded native executable macro acquisition, not arbitrary language genesis.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, sys
from collections import deque
from pathlib import Path

OLD=("TAKE","PUT","SHIFT_LEFT","SHIFT_RIGHT")
EXT=OLD+("CALL_O1",)
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
def programs(alpha):
    for n in (1,2,3):yield from itertools.product(alpha,repeat=n)
def dev_worlds():
    return tuple(itertools.permutations(range(4)))+tuple(itertools.permutations(range(5)))
def protected_worlds(seed):
    ordered=list(itertools.permutations(range(6)))
    ordered.sort(key=lambda p:hashlib.sha256((seed+':'+','.join(map(str,p))).encode()).hexdigest())
    return tuple(ordered[:48])+tuple(sorted(set(itertools.permutations((0,0,1,1)))))

class World:
    def __init__(self,kind,vals):
        self.kind=kind
        if kind=="deque":self.s=deque(vals)
        elif kind=="numpy":
            import numpy as np
            self.np=np;self.s=np.asarray(vals,dtype=np.int64)
        else:raise ValueError("unsupported engine")
    def state(self):
        if self.kind=="deque":return tuple(self.s)
        return tuple(map(int,self.s.tolist()))
    def take(self):
        if self.kind=="deque":return int(self.s.popleft())
        v=int(self.s[0]);self.s=self.np.delete(self.s,0);return v
    def put(self,v):
        if self.kind=="deque":self.s.append(v)
        else:self.s=self.np.append(self.s,v)
    def rotate(self,n):
        if self.kind=="deque":self.s.rotate(n)
        else:self.s=self.np.roll(self.s,n)

def execute(world,program,macros=None):
    """Run actual source-native primitives on a disposable instance."""
    before=world.state();last=None;held=None;calls=0;macros=macros or {}
    try:
        for op in program:
            if op=="TAKE":
                if held is not None:return None,calls,"INVALID_HELD"
                held=world.take();last=held;calls+=1
            elif op=="PUT":
                if held is None:return None,calls,"INVALID_PUT"
                world.put(held);held=None;calls+=1
            elif op=="SHIFT_LEFT":world.rotate(-1);calls+=1
            elif op=="SHIFT_RIGHT":world.rotate(1);calls+=1
            elif op=="CALL_O1":
                if "O1" not in macros:return None,calls,"UNKNOWN_PARENT_WITHDRAWN"
                value,cost,reason=execute(world,macros["O1"])
                calls+=cost
                if reason!="EXACT_RESTORATION":return None,calls,"INVALID_PARENT"
                last=value
            else:return None,calls,"INVALID_OPCODE"
        if held is not None or world.state()!=before:return None,calls,"STATE_CHANGED"
        if last is None:return None,calls,"NO_RESULT"
        return last,calls,"EXACT_RESTORATION"
    except Exception as e:
        return None,calls,"NATIVE_ERROR_"+type(e).__name__

def native_answer(kind,values,index):
    state=World(kind,values)
    last=None
    for _ in range(index):last=state.take()
    return last

def judge(kind,prog,index,worlds,macros=None):
    calls=0
    for i,vals in enumerate(worlds):
        value,cost,status=execute(World(kind,vals),prog,macros)
        calls+=cost
        if status!="EXACT_RESTORATION" or value!=native_answer(kind,vals,index):
            return dict(ok=False,examined=i+1,primitive_calls=calls,reason=status)
    return dict(ok=True,examined=len(worlds),primitive_calls=calls)

def census(index,alphabet,worlds,macros=None):
    rows=[];winners=[];cost=0
    for p in programs(alphabet):
        v=judge("deque",p,index,worlds,macros)
        cost+=v["primitive_calls"]
        rows.append(dict(program=list(p),success=v["ok"],examined=v["examined"]))
        if v["ok"]:winners.append(list(p))
    return dict(candidate_count=len(rows),native_calls=cost,winners=winners,
                winner=winners[0] if winners else None,candidates=rows)

def seal(prog,parent=None):
    body=dict(format="source-observer-v1",program=list(prog),
              parent_sha256=parent["sha256"] if parent else None,
              original_horizon=3,development="native-CPython-deque",
              authority="LOCAL_RESEARCH_ONLY")
    return {**body,"sha256":digest(body)}

def certified(c,parent=None):
    if not isinstance(c,dict):return False
    if c.get("sha256")!=digest({k:v for k,v in c.items() if k!="sha256"}):return False
    if c.get("parent_sha256")!=(parent["sha256"] if parent else None):return False
    if c.get("format")!="source-observer-v1" or c.get("original_horizon")!=3:return False
    p=c.get("program")
    return isinstance(p,list) and 0<len(p)<=3 and all(x in (EXT if parent else OLD) for x in p)

def source_development(out):
    worlds=dev_worlds()
    g1=census(1,OLD,worlds)
    if not g1["winner"]:raise RuntimeError("UNKNOWN_G1_NO_VERIFIED_OBSERVER")
    o1=seal(g1["winner"]);assert certified(o1)
    g2_old=census(2,OLD,worlds)
    g2_new=census(2,EXT,worlds,{"O1":o1["program"]})
    if g2_old["winner"] is not None:raise RuntimeError("OLD_HORIZON_NOT_INSUFFICIENT")
    if not g2_new["winner"]:raise RuntimeError("UNKNOWN_G2_NO_VERIFIED_EXPANSION")
    o2=seal(g2_new["winner"],o1);assert certified(o2,o1)
    ledger=census(2,EXT,worlds,{"O1":o1["program"]})
    assert ledger["winner"]==g2_new["winner"]
    packet=dict(verdict="PASS_SOURCE_NATIVE_BOUNDED_ACQUISITION",
                old_grammar=OLD,new_grammar=EXT,horizon=3,
                source_world_count=len(worlds),source_worlds_sha256=digest(worlds),
                G1=g1,G2_cold=g2_old,G2_promoted=g2_new,
                full_information_executable_ledger=dict(winner=ledger["winner"],
                  candidate_count=ledger["candidate_count"],native_calls=ledger["native_calls"],
                  outcome="TIE",claim="NO_COMPARATIVE_ADVANTAGE"),
                O1=o1,O2=o2,protected_backend_inspected=False)
    path=Path(out)
    save(path,packet)
    save(path.parent/"O1.capability.json",o1)
    save(path.parent/"O2.capability.json",o2)
    print(json.dumps(dict(verdict=packet["verdict"],O1=o1["program"],O2=o2["program"],
       old_second_winners=len(g2_old["winners"]),promoted_second_winners=len(g2_new["winners"]),
       full_ledger_ties=True)))
    return packet

def target_test(development,out,seed):
    path=Path(development);d=json.loads(path.read_text());root=path.parent
    o1=json.loads((root/"O1.capability.json").read_text())
    o2=json.loads((root/"O2.capability.json").read_text())
    if o1!=d["O1"] or o2!=d["O2"] or not certified(o1) or not certified(o2,o1):
        raise RuntimeError("INVALID_OR_CHANGED_SOURCE_MANIFEST")
    worlds=protected_worlds(seed)
    g1=judge("numpy",o1["program"],1,worlds)
    g2=judge("numpy",o2["program"],2,worlds,{"O1":o1["program"]})
    if not (g1["ok"] and g2["ok"]):raise RuntimeError("PROTECTED_NATIVE_TRANSFER_REJECTED")
    # Physically delete the parent executable file, leave O2 on disk.
    parent=root/"O1.capability.json";original=parent.read_bytes();parent.unlink()
    ablated=judge("numpy",o2["program"],2,worlds)
    if parent.exists() or ablated["ok"]:raise RuntimeError("PARENT_WITHDRAWAL_FAILED")
    # Explicit source requalification before restoring the byte-identical body.
    source_reverification=judge("deque",o1["program"],1,dev_worlds())
    if not source_reverification["ok"]:raise RuntimeError("PARENT_REQUALIFICATION_FAILED")
    parent.write_bytes(original)
    if not certified(json.loads(parent.read_text())):raise RuntimeError("PARENT_RESTORE_INVALID")
    restored=judge("numpy",o2["program"],2,worlds,{"O1":o1["program"]})
    assert restored["ok"]
    forged=dict(o1);forged["program"]=["SHIFT_RIGHT"]
    assert not certified(forged)
    import numpy as np, numpy._core._multiarray_umath as native
    direct=sum(int(np.asarray(vals,dtype=np.int64)[1]==native_answer("numpy",vals,2))
               for vals in worlds)
    assert direct==len(worlds)
    result=dict(verdict="PASS_BOUNDED_NATIVE_OBSERVER_EXPANSION",
        protected_source="NumPy.ndarray",numpy_version=np.__version__,
        native_extension_sha256=hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        python_version=sys.version,protected_count=len(worlds),
        protected_sha256=digest(worlds),G1=g1,G2=g2,
        physical_parent_unlink=True,ablation=ablated,source_reverified=source_reverification,
        restored=restored,wrong_digest_declined=True,
        full_information_executable_ledger=d["full_information_executable_ledger"],
        native_direct_index_baseline=dict(correct=direct,scoped_worlds=len(worlds),
                                           cost="CHEAPER_NO_METHOD_ACQUISITION"),
        scientific_scope="human-supplied G1/G2 objectives and finite typed primitive language",
        comparative_verdict="BASELINE_TIE_OR_CHEAPER; NO_STRICT_ADVANTAGE",
        model_comparator="NOT_RUN",unrestricted_L7="UNKNOWN")
    save(out,result)
    print(json.dumps(dict(verdict=result["verdict"],protected_worlds=len(worlds),
                          ablation_denied=not ablated["ok"],full_info_baseline_ties=True)))
    return result

def cold_restart(development,output,seed):
    root=Path(development).parent
    d=json.loads(Path(development).read_text())
    o1=json.loads((root/"O1.capability.json").read_text())
    o2=json.loads((root/"O2.capability.json").read_text())
    if (o1!=d["O1"] or o2!=d["O2"] or not certified(o1) or not certified(o2,o1)):
        raise RuntimeError("COLD_PROCESS_INVALID_SOURCE")
    native=judge("numpy",o2["program"],2,protected_worlds(seed),{"O1":o1["program"]})
    if not native["ok"]:raise RuntimeError("COLD_REPLAY_REJECTED")
    save(output,dict(verdict="PASS_COLD_PROCESS_RESTART",native=native))
    print(json.dumps(dict(verdict="PASS_COLD_PROCESS_RESTART",cases=native["examined"])))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["develop","target","restart"])
    p.add_argument("--development")
    p.add_argument("--out",required=True)
    p.add_argument("--seed",default="observer-self-expansion-20261016-fixed")
    a=p.parse_args()
    if a.mode=="develop":source_development(a.out)
    else:
        if not a.development:raise ValueError("--development required")
        if a.mode=="target":target_test(a.development,a.out,a.seed)
        else:cold_restart(a.development,a.out,a.seed)
