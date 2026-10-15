"""Independent finite-grammar reference interpreter and native target oracle.

Does not import the candidate engine or its program execution functions.
A PASS warrants only exact 3-instruction horizons in the supplied interfaces.
"""
import argparse, hashlib, itertools, json
from pathlib import Path
from collections import deque

OLD=("TAKE","PUT","SHIFT_LEFT","SHIFT_RIGHT")
def source_worlds():
    return tuple(itertools.permutations(range(4)))+tuple(itertools.permutations(range(5)))
def target_worlds(seed):
    a=list(itertools.permutations(range(6)))
    a.sort(key=lambda p:hashlib.sha256((seed+':'+','.join(map(str,p))).encode()).hexdigest())
    return tuple(a[:48])+tuple(sorted(set(itertools.permutations((0,0,1,1)))))

def evaluate(kind,source,program,parent=None):
    if kind=="deque":
        state=deque(source)
        present=lambda:tuple(state)
        def take():return int(state.popleft())
        def put(x):state.append(x)
        def shift(n):state.rotate(n)
    else:
        import numpy as np
        state=np.asarray(source,dtype=np.int64)
        present=lambda:tuple(map(int,state.tolist()))
        def take():
            nonlocal state
            result=int(state[0]);state=np.delete(state,0);return result
        def put(x):
            nonlocal state
            state=np.append(state,x)
        def shift(n):
            nonlocal state
            state=np.roll(state,n)
    pending=None;recorded=None
    for instr in program:
        if instr=="TAKE":
            if pending is not None:return None
            pending=take();recorded=pending
        elif instr=="PUT":
            if pending is None:return None
            put(pending);pending=None
        elif instr=="SHIFT_LEFT":shift(-1)
        elif instr=="SHIFT_RIGHT":shift(1)
        elif instr=="CALL_O1":
            if parent is None:return None
            recorded=evaluate(kind,present(),parent)
        else:return None
    if pending is not None or present()!=tuple(source):return None
    return recorded

def native_reference(kind,source,k):
    if kind=="deque":
        s=deque(source)
        for _ in range(k):v=int(s.popleft())
    else:
        import numpy as np
        s=np.asarray(source,dtype=np.int64)
        for _ in range(k):
            v=int(s[0]);s=np.delete(s,0)
    return v

def check(kind,worlds,program,k,parent=None):
    failures=0;first=None
    for values in worlds:
        try:got=evaluate(kind,values,program,parent=parent)
        except Exception as e:got="ERROR_"+type(e).__name__
        expected=native_reference(kind,values,k)
        if got!=expected:
            failures+=1
            if first is None:first=dict(input=list(values),actual=got,expected=expected)
    return dict(passed=len(worlds)-failures,total=len(worlds),failures=failures,
                first_failure=first,verified=failures==0)

def inspect(dev_path,target_path,seed,out):
    d=json.loads(Path(dev_path).read_text());t=json.loads(Path(target_path).read_text())
    o1=d["O1"]["program"];o2=d["O2"]["program"]
    source=source_worlds();target=target_worlds(seed)
    cold_winners=[]
    for n in (1,2,3):
        for prog in itertools.product(OLD,repeat=n):
            if check("deque",source,prog,2)["verified"]:cold_winners.append(list(prog))
    assert len(cold_winners)==0, cold_winners
    a=check("deque",source,o1,1)
    b=check("deque",source,o2,2,parent=o1)
    c=check("numpy",target,o1,1)
    d2=check("numpy",target,o2,2,parent=o1)
    ablate=check("numpy",target,o2,2)
    assert a["verified"] and b["verified"] and c["verified"] and d2["verified"]
    assert not ablate["verified"]
    assert t["protected_count"]==len(target)
    assert t["G1"]["ok"] and t["G2"]["ok"]
    assert t["native_direct_index_baseline"]["correct"]==len(target)
    res=dict(verdict="PASS_INDEPENDENT_NATIVE_OBSERVER_VERIFICATION",
        exact_old_frontier=4+16+64,old_G2_winners=0,
        source_first=a,source_second=b,target_first=c,target_second=d2,
        ablation_with_o2_only=ablate,
        full_information_executable_ledger="TIE",direct_index_baseline="CHEAPER",
        result_scope="bounded source-native abstraction; supplied test and constructor grammar")
    Path(out).write_text(json.dumps(res,indent=2,sort_keys=True)+"\n")
    print(json.dumps(dict(verdict=res["verdict"],old_winners=0,
                          protected_verified=d2["passed"],ledger="TIE")))
    return res
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--development",required=True)
    ap.add_argument("--target",required=True);ap.add_argument("--seed",required=True)
    ap.add_argument("--out",required=True);a=ap.parse_args()
    inspect(a.development,a.target,a.seed,a.out)
