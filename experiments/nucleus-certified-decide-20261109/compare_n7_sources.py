"""Compare exact Lean source definitions across original vs alternative NDJSON.

This is structural evidence only; hashes of normalized expressions are neither
proof certificates nor a substitute for the checker.
"""
from __future__ import annotations
import hashlib,json,pathlib,sys
EXPECTED_ORIG="abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
EXPECTED_ALT="8330840c6fc2af2b5a91d10b32aa331676271bde70701b354bdab3d270f1d902"
REQUIRED=("EquationLHS","EquationRHS","Goal","Magma.op","countermodel.op","countermodel.inst")

class Export:
    def __init__(self,src:bytes):
        self.meta=json.loads(src.splitlines()[0])["meta"]
        self.names={}
        self.exprs={}
        self.levels={}
        self.decls={}
        for line in src.splitlines():
            rec=json.loads(line)
            if "in" in rec:self.names[int(rec["in"])]=rec
            if "ie" in rec:self.exprs[int(rec["ie"])]=rec
            if "il" in rec:self.levels[int(rec["il"])]=rec
            for kind in ("def","thm","opaque","axiom"):
                if kind in rec:
                    d=rec[kind]
                    self.decls[self.name(int(d["name"]))]=(kind,d)
        self.memo={}
        self.level_memo={}
    def name(self,idx):
        stack=[];seen=set()
        while idx!=0:
            if idx in seen or idx not in self.names:raise ValueError("missing or cyclic name")
            seen.add(idx)
            r=self.names[idx]
            if "str" in r:
                stack.append(str(r["str"]["str"]))
                idx=int(r["str"]["pre"])
            elif "num" in r:
                stack.append(str(r["num"]["i"]))
                idx=int(r["num"]["pre"])
            else:raise ValueError("name tag")
        return ".".join(reversed(stack))
    def level(self,i):
        if i==0:return ["zero"]
        if i in self.level_memo:return self.level_memo[i]
        a=self.levels[i]
        if "succ" in a:o=["succ",self.level(int(a["succ"]))]
        elif "max" in a:o=["max"]+[self.level(int(x)) for x in a["max"]]
        elif "imax" in a:o=["imax"]+[self.level(int(x)) for x in a["imax"]]
        elif "param" in a:o=["param",self.name(int(a["param"]))]
        else:raise ValueError("unknown level")
        self.level_memo[i]=o
        return o
    def expr(self,i):
        if i in self.memo:return self.memo[i]
        a=self.exprs[i]
        if "bvar" in a:o=["bvar",int(a["bvar"])]
        elif "natVal" in a:o=["nat",str(a["natVal"])]
        elif "strVal" in a:o=["string",str(a["strVal"])]
        elif "sort" in a:o=["sort",self.level(int(a["sort"]))]
        elif "const" in a:
            c=a["const"];o=["const",self.name(int(c["name"])),[self.level(int(j)) for j in c.get("us",[])]]
        elif "app" in a:
            c=a["app"];o=["app",self.expr(int(c["fn"])),self.expr(int(c["arg"]))]
        elif "lam" in a or "forallE" in a:
            k="lam" if "lam" in a else "forallE";c=a[k]
            o=[k,c.get("binderInfo","default"),self.expr(int(c["type"])),self.expr(int(c["body"]))]
        elif "letE" in a:
            c=a["letE"];o=["let",self.expr(int(c["type"])),self.expr(int(c["value"])),self.expr(int(c["body"])),c.get("nondep")]
        elif "proj" in a:
            c=a["proj"];o=["proj",self.name(int(c["typeName"])),int(c["idx"]),self.expr(int(c["struct"]))]
        elif "mdata" in a:
            o=self.expr(int(a["mdata"]["expr"]))
        else:raise ValueError("unknown expr tag "+repr(a))
        self.memo[i]=o
        return o
    def fingerprint(self,name,field):
        kind,d=self.decls[name]
        if field not in d:raise ValueError("missing field "+field+" in "+name)
        can=self.expr(int(d[field]))
        return hashlib.sha256(json.dumps(can,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def compare(original,alternative):
    if hashlib.sha256(original).hexdigest()!=EXPECTED_ORIG:raise ValueError("original SHA drift")
    if hashlib.sha256(alternative).hexdigest()!=EXPECTED_ALT:raise ValueError("alternative SHA drift")
    o=Export(original);a=Export(alternative)
    if o.meta["lean"]!=a.meta["lean"]:raise ValueError("Lean source version mismatch")
    if o.meta["format"]!=a.meta["format"]:raise ValueError("export protocol mismatch")
    checks={}
    for name in REQUIRED:
        if name not in o.decls or name not in a.decls:raise ValueError("missing required common declaration "+name)
        kind1,d1=o.decls[name];kind2,d2=a.decls[name]
        kinds_equal=(kind1==kind2)
        ty_equal=o.fingerprint(name,"type")==a.fingerprint(name,"type")
        value_equal=("value" not in d1 and "value" not in d2) or (
          "value" in d1 and "value" in d2 and o.fingerprint(name,"value")==a.fingerprint(name,"value"))
        level_params_equal=([o.name(int(x)) for x in d1.get("levelParams",[])]==
                            [a.name(int(x)) for x in d2.get("levelParams",[])])
        checks[name]={"kind_equal":kinds_equal,"type_equal":ty_equal,
                      "value_equal":value_equal,"universe_parameters_equal":level_params_equal,
                      "original_type_sha256":o.fingerprint(name,"type"),
                      "alternative_type_sha256":a.fingerprint(name,"type")}
    if "countermodel" not in o.decls or "algebraicCountermodel" not in a.decls:
        raise ValueError("missing original/alternate proposition")
    same_proposition=(o.fingerprint("countermodel","type")==a.fingerprint("algebraicCountermodel","type"))
    if not all(all(row[k] for k in ("kind_equal","type_equal","value_equal","universe_parameters_equal"))
       for row in checks.values()) or not same_proposition:
        raise ValueError("source proposition/operation structural mismatch: "+json.dumps(checks,sort_keys=True))
    return {"original_sha256":EXPECTED_ORIG,"alternative_sha256":EXPECTED_ALT,
            "lean_version":o.meta["lean"],"matched_declarations":checks,
            "same_proposition":same_proposition,"not_a_kernel_verification_certificate":True,
            "original_verdict_unchanged":"UNKNOWN"}

if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("usage: compare_n7_sources.py original.ndjson alternative.ndjson out.json")
    out=compare(pathlib.Path(sys.argv[1]).read_bytes(),pathlib.Path(sys.argv[2]).read_bytes())
    pathlib.Path(sys.argv[3]).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("N7_EXACT_SOURCE_BRIDGE="+json.dumps({"same_proposition":out["same_proposition"],
       "all_declarations_equal":len(out["matched_declarations"]),"names":sorted(out["matched_declarations"]),
       "nucleus_original_verdict":out["original_verdict_unchanged"]},sort_keys=True))
