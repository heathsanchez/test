"""Create precisely one-declaration invalid mutants of a pinned Lean NDJSON export.

This code does not generate proofs or authorize acceptance. It retains every
non-target record byte-for-byte and emits two intentional type/value forgeries.
"""
from __future__ import annotations
import hashlib, json, pathlib, sys

ORIGINAL_SHA = "8330840c6fc2af2b5a91d10b32aa331676271bde70701b354bdab3d270f1d902"

def resolve_name(idx, names):
    seen=set()
    parts=[]
    while idx != 0:
        if idx in seen or idx not in names: raise ValueError("missing/cyclic name prefix")
        seen.add(idx)
        r=names[idx]
        if "str" in r:
            parts.append(str(r["str"]["str"]))
            idx=int(r["str"]["pre"])
        elif "num" in r:
            parts.append(str(r["num"]["i"]))
            idx=int(r["num"]["pre"])
        else: raise ValueError("invalid name type")
    return ".".join(reversed(parts))

def mutate(data: bytes):
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("alternative export source identity drift")
    lines=data.splitlines(keepends=True)
    records=[json.loads(x) for x in lines]
    names={int(r["in"]):r for r in records if "in" in r}
    defs=[(i,r["def"]) for i,r in enumerate(records)
          if "def" in r and resolve_name(int(r["def"]["name"]),names)=="algebraicCountermodel"]
    if len(defs)!=1:raise ValueError("algebraicCountermodel not uniquely found")
    index,stmt=defs[0]
    false_const=[int(r["ie"]) for r in records
        if "ie" in r and "const" in r
        and resolve_name(int(r["const"]["name"]),names)=="False"
        and not r["const"].get("us")]
    nat_zero=[int(r["ie"]) for r in records
        if "ie" in r and "natVal" in r and str(r["natVal"])=="0"]
    if not false_const or not nat_zero:
        raise ValueError("missing existing False/Nat-zero terms; do not fabricate refs")
    if int(stmt["type"]) in false_const or int(stmt["value"]) in nat_zero:
        raise ValueError("mutation did not change target")
    result={}
    for label,key,new_id in (
        ("forged_false_claim","type",false_const[0]),
        ("forged_nat_zero_proof","value",nat_zero[0])
    ):
        edited=json.loads(lines[index])
        edited["def"][key]=new_id
        new_line=json.dumps(edited,separators=(",",":"),ensure_ascii=False).encode()
        if lines[index].endswith(b"\n"):new_line+=b"\n"
        mutated=lines[:index]+[new_line]+lines[index+1:]
        payload=b"".join(mutated)
        check=[i for i,(a,b) in enumerate(zip(lines,mutated)) if a!=b]
        if check!=[index]:raise ValueError("mutation modified multiple records")
        result[label]={
            "data":payload,
            "sha256":hashlib.sha256(payload).hexdigest(),
            "target_record_index":index,
            "mutated_field":key,
            "old_expr":int(stmt[key]),
            "new_expr":new_id,
            "only_one_record_modified":True
        }
    return result

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: forge_algebraic.py input.ndjson out_dir")
    src=pathlib.Path(sys.argv[1]).read_bytes()
    out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    mutants=mutate(src)
    manifest={}
    for name,record in mutants.items():
        (out/(name+".ndjson")).write_bytes(record["data"])
        manifest[name]={key:value for key,value in record.items() if key!="data"}
    (out/"forgeries.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print("N7_FORGERIES="+json.dumps(manifest,sort_keys=True))
