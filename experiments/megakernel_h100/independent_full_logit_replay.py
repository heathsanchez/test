"""Independent CPU re-evaluation of all retained full16 BF16 logits.

Reconstructs exact worker-emitted output bits and recomputes all 128256
element differences per case. Not an independent CUDA/model execution.
"""
import argparse, base64, hashlib, heapq, json, math, re, struct, zlib
from pathlib import Path
from independent_consequence_assurance import audit as audit_witnesses, load_json, PLAN, ATOL, RTOL

N=128256
BYTES=N*2
def demand(x, why):
    if not x: raise ValueError("REJECTED_FULL_LOGIT_REPLAY: "+why)
def f32(x): return struct.unpack("<f",struct.pack("<f",x))[0]

def decode(rec):
    demand(isinstance(rec,dict) and rec.get("dtype")=="bf16-le" and
           rec.get("elements")==N and rec.get("raw_bytes")==BYTES, "dtype/shape")
    b64=rec.get("zlib_base64")
    demand(type(b64) is str and len(b64)<=365000, "encoded length")
    demand(type(rec.get("compressed_bytes")) is int and 0<rec["compressed_bytes"]<=270000, "compressed bytes")
    demand(type(rec.get("raw_sha256")) is str and
           re.fullmatch("[a-f0-9]{64}",rec["raw_sha256"]) is not None, "hash shape")
    try:
        blob=base64.b64decode(b64,validate=True)
        demand(len(blob)==rec["compressed_bytes"], "compressed byte count")
        stream=zlib.decompressobj()
        raw=stream.decompress(blob,BYTES+1)
        demand(stream.eof and not stream.unconsumed_tail and not stream.unused_data,"zlib trailing/incomplete")
        raw+=stream.flush()
    except (ValueError,zlib.error) as e:
        raise ValueError("REJECTED_FULL_LOGIT_REPLAY: malformed payload") from e
    demand(len(raw)==BYTES and hashlib.sha256(raw).hexdigest()==rec["raw_sha256"], "raw payload integrity")
    floats=[struct.unpack("<f",struct.pack("<I",bits<<16))[0]
            for (bits,) in struct.iter_unpack("<H",raw)]
    demand(len(floats)==N and all(math.isfinite(x) for x in floats), "nonfinite or truncated logits")
    return floats

def replay(case):
    raw=case.get("raw_logits_bf16")
    demand(type(raw) is dict and set(raw)=={"reference","native"},"missing raw pair")
    ref=decode(raw["reference"]); gpu=decode(raw["native"])
    maxerr=0.0; violations=0; first=[]
    for i,(a,b) in enumerate(zip(ref,gpu)):
        err=abs(a-b); allowed=f32(f32(ATOL)+f32(f32(RTOL)*abs(a)))
        maxerr=max(maxerr,err)
        if err>allowed:
            violations+=1
            if len(first)<8:
                first.append((i,a,b,err,allowed))
    m=case["fields"]["logits"]
    demand(m["violations"]==violations and m["nonfinite"]==0, "replayed logit violation count")
    demand(abs(m["max_abs_diff"]-maxerr)<=1e-6,"replayed max difference")
    witness=m.get("first_violations",[])
    demand(len(witness)==len(first),"missing/extra failing samples")
    for c,expected in zip(witness,first):
        demand(c["flat_index"]==expected[0],"witness index")
        for field,actual in zip(("reference","gpu","abs_error","allowed_error"),expected[1:]):
            demand(abs(c[field]-actual)<=1e-6,"witness scalar mismatch")
    choice=case["logit_choice"]
    refbest=max(range(N),key=ref.__getitem__)
    gpubest=max(range(N),key=gpu.__getitem__)
    demand(choice["reference_top1"]==refbest and choice["native_top1"]==gpubest,
           "top token mismatch against entire vector")
    demand(choice["top1_equal"] is (refbest==gpubest),"reported agreement mismatch")
    r2=heapq.nlargest(2,ref); g2=heapq.nlargest(2,gpu)
    demand(abs(choice["reference_top1_margin"]-(r2[0]-r2[1]))<=1e-6,"reference runner-up gap")
    demand(abs(choice["native_top1_margin"]-(g2[0]-g2[1]))<=1e-6,"GPU runner-up gap")
    for name,vec in (("reference_top5",ref),("native_top5",gpu)):
        vals=[vec[i] for i in choice[name]]
        demand(all(vals[i]>=vals[i+1] for i in range(4)),"top5 out of order")
        demand(abs(vals[-1]-heapq.nlargest(5,vec)[-1])<=1e-6,"top5 not global")
    candidates=choice["candidate_logits"]
    demand([x["index"] for x in candidates]==
           sorted(set(choice["reference_top5"])|set(choice["native_top5"])),"candidate membership")
    for entry in candidates:
        idx=entry["index"]
        demand(abs(entry["reference"]-ref[idx])<=1e-6 and
               abs(entry["native"]-gpu[idx])<=1e-6,"paired values mismatch")
    slack=gpu[refbest]-(r2[1]+maxerr)
    return {"elements_checked":N,"tolerance_violations":violations,"max_abs_error":maxerr,
            "reference_top1":refbest,"native_top1":gpubest,
            "top1_equal":refbest==gpubest,"reference_margin":r2[0]-r2[1],
            "sufficient_one_sided_rank_margin":slack>0,"margin_slack":slack,
            "reference_raw_sha256":raw["reference"]["raw_sha256"],
            "native_raw_sha256":raw["native"]["raw_sha256"]}

def audit(report):
    base=audit_witnesses(report)
    cases={key:replay(report["checks"][key]) for key in PLAN}
    return {"schema":"mathgraph-h100-full-logit-vector-replay-v1",
            "status":"FULL_BF16_LOGIT_VECTOR_REPLAYED_NOT_INDEPENDENT_GPU_EXECUTION",
            "source_pin":base["source_pin"],"cases_checked":len(PLAN),
            "pairs_of_logits_replayed":len(PLAN)*N,
            "top1_agreements":sum(x["top1_equal"] for x in cases.values()),
            "sufficient_ranking_margins":sum(x["sufficient_one_sided_rank_margin"] for x in cases.values()),
            "cases":cases,
            "trusted_boundary":"worker-emitted raw BF16 bits replayed on CPU; GPU execution and model weights not independently reproduced"}

def main():
    p=argparse.ArgumentParser();p.add_argument("evidence",type=Path);p.add_argument("--out",type=Path)
    args=p.parse_args()
    out=json.dumps(audit(load_json(args.evidence)),indent=2,sort_keys=True)+"\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(out)
    print(out,end="")
if __name__=="__main__":main()
