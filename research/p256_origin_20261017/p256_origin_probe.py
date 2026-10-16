#!/usr/bin/env python3
"""Exact, bounded historical-origin probe for NIST P-256 generator G.

Research status: calibration + NEGATIVE/UNKNOWN until an exact point witness is found.
All search restrictions are reported; absence of a hit never proves historical origin impossible.

External historical source (retrieved 2026-10-17):
  https://www.anthropic.com/research/ecdsa-curve-origins (2026-10-16)
Curve parameters: local OpenSSL explicit named curve output.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

M = 2**107 - 1
A = pow(3, 121, M)
MASK26 = (1 << 26) - 1
LCG_MASK = (1 << 48) - 1
LCG_A = 0x5DEECE66D
LCG_C = 0xB
P192 = 2**192 - 2**64 - 1
P239 = 2**239 - 2**143 - 2**95 + 2**47 - 1

# The six published FreeLIP / early NTL positive controls, exactly as published.
CALIBRATION = [
    ("prime192v1", 20000, P192, 0x64210519e59c80e70fa7e9ab72243049feb8deecc146b9b1, 0x188da80eb03090f67cbf20eb43a18800f4ff0afd82ff1012, 2),
    ("prime239v1", 20420, P239, 0x6b016c3bdcf18941d0d654921475ca71a9db2fb27d1d37796185c2942c0a, 0xffa963cdca8816ccc33b8642bedf905c3d358573d3f27fbbd3b3cb9aaaf, 3),
    ("prime239v2", 20507, P239, 0x617fab6832576cbbfed50d99f0249c3fee58b94ba0038c7ae84c8c832f2c, 0x38af09d98727705120c921bb5e9e26296a3cdcf2f35757a0eafd87b830e7, 2),
    ("prime239v3", 20509, P239, 0x255705fa2a306654b1f4cb03d6a750a30c250102d4988717d9ba15ab6d3e, 0x6768ae8e18bb92cfcf005c949aa2c6d94853d0e660bbf854b1c9505fe95a, 1),
    ("prime192v2", 20512, P192, 0xcc22d6dfb95c6b25e49c0d6364a4e5980c393aa21668d953, 0xeea2bae7e1497842f2de7769cfe9c989c072ad696f48034a, 5),
    ("prime192v3", 20517, P192, 0x22123dc2395a05caa7423daeccc94760a7d462256bd56916, 0x7d29778100c65a1da1783716588dce2b8b4aee8e228f1896, 1),
]

PRIME_SEEDS = {
    "prime239v1": ("1997-05-15 15:49:03", 2185, "E43BB460F0B80CC0C0B075798E948060F8321B7D"),
    "prime239v2": ("1997-05-15 15:49:03", 2320, "E8B4011604095303CA3B8099982BE09FCB9AE616"),
    "prime239v3": ("1997-05-15 15:49:03", 3048, "7D7374168FFE3471B60A857686A19475D3BFA2FF"),
    "P-192": ("1997-05-18 14:45:34", 139, "3045AE6FC8422F64ED579528D38120EAE12196D5"),
    "prime192v3": ("1997-05-18 14:45:34", 5228, "C469684435DEB378C4B65CA9591E2A5763059A2E"),
    "prime192v2": ("1997-05-18 14:45:34", 6013, "31A92EE2029FD10D901B113E990710F0D21AC6B6"),
    "P-521": ("1997-08-08 01:12:04", 1136, "D09E8800291CB85396CC6717393284AAA0DA64BA"),
    "P-256": ("1997-08-16 01:52:34", 1842, "C49D360886E704936A6678E1139D26B7819F7E90"),
    "P-384": ("1997-08-30 14:50:08", 2688, "A335926AA319A27A1D00896A6773A4827ACDAC73"),
    "P-224": ("1998-04-03 12:52:07", 7026, "BD71344799D5C7FCDC45B59FA3B9AB8F6A948BC5"),
}
BINARY_SEEDS = {
    "B-233": ("1998-04-17 15:24:18", 155, "74D59FF07F6B413D0EA14B344B20A2DB049B50C3"),
    "B-283": ("1998-04-17 15:27:44", 32, "77E2B07370EB0F832A6DD5B62DFC88CD06BB84BE"),
    "B-409": ("1998-04-17 15:30:18", 60, "4099B5A457F9D69F79213D094C4BCD4D4262210B"),
    "B-571": ("1998-04-17 15:32:08", 73, "2AA058F73A0E33AB486B0F610410C53A7F132310"),
}


def unix(s):
    return int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone.utc).timestamp())


def lcg_candidate(time_seed, n, per, shift, width):
    x = (time_seed << 16) | 0x330E
    out = []
    for i in range(per*n):
        x = (LCG_A * x + LCG_C) & LCG_MASK
        if i >= per*(n-1):
            out.append(f"{x >> shift:0{width}X}")
    return "".join(out)


def zrandom_x(seed, p, b, *, warmup=7, limbs_delta=1, max_tries=30):
    state = seed
    def limb():
        nonlocal state
        state = state * A % M
        return state & MASK26
    for _ in range(warmup):
        limb()
    limbcount = (p.bit_length() + 25)//26 + limbs_delta
    for tries in range(1, max_tries+1):
        raw = 0
        for _ in range(limbcount):
            raw = (raw << 26) | limb()
        x = raw % p
        f = (pow(x, 3, p) - 3*x + b) % p
        if pow(f, (p-1)//2, p) == 1:
            return x, tries
    return None, None


def parse_openssl_curve(name):
    try:
        raw = subprocess.check_output(["openssl", "ecparam", "-name", name, "-param_enc", "explicit", "-text", "-noout"], text=True)
    except Exception as exc:
        raise RuntimeError(f"OpenSSL ecparam failed for {name}: {exc}") from exc
    sections = {}
    active = None
    for line in raw.splitlines():
        if line.startswith("Prime:") or line.startswith("A:") or line.startswith("B:") or line.startswith("Generator (uncompressed):") or line.startswith("Order:") or line.startswith("Seed:"):
            active = line.split(":")[0]
            sections[active] = []
            # A/B can be decimal or hex inline on some OpenSSL versions.
            tail = line.split(":", 1)[1].strip()
            if tail and not tail.endswith("(0x0)"):
                sections[active].append(tail)
        elif active and line.startswith("    "):
            sections[active].append(line.strip())
        else:
            active = None
    def num(key):
        v = "".join(sections[key]).replace(":", "").replace(" ", "")
        if "(0x" in v:
            v = v[v.find("(0x")+3:v.find(")")]
        return int(v,16)
    p, a, b, G, n = num("Prime"), num("A"), num("B"), num("Generator (uncompressed)"), num("Order")
    N = (p.bit_length()+7)//8
    gb = G.to_bytes(2*N+1,"big")
    if gb[0] != 4:
        raise AssertionError("expected uncompressed point")
    gx,gy = int.from_bytes(gb[1:N+1],"big"), int.from_bytes(gb[N+1:],"big")
    if (gy*gy-(pow(gx,3,p)+a*gx+b))%p != 0:
        raise AssertionError("point not on curve")
    return {"curve":name,"p":p,"a":a,"b":b,"gx":gx,"gy":gy,"n":n,"seed":sections.get("Seed"),"openssl_sha256":hashlib.sha256(raw.encode()).hexdigest()}


def scan_freelip_small_seeds(curve, seed_limit=65536, prefix_draws=192, limb_counts=(10,11), limb_modes=("low26","high26"), orders=("msf","lsf")):
    """Exhaustive within exact domain: contiguous 26-bit windows of first prefix_draws PRNG outputs.
    Includes all warmups <= 15 and first >= 15 attempts for both 10/11 limbs.
    Checks ANY window matching target, even if prior curve-point would have stopped search.
    """
    p, target=curve["p"],curve["gx"]
    counts = {f"{m}/{L}/{o}":0 for m in limb_modes for L in limb_counts for o in orders}
    hits=[]
    total=0
    start=time.monotonic()
    MASK26=(1<<26)-1
    for seed in range(seed_limit):
        state=seed
        low=[]; high=[]
        for j in range(prefix_draws):
            state=state*A % M
            low.append(state&MASK26)
            high.append(state >> (107-26))
        for mode in limb_modes:
            outputs=low if mode=="low26" else high
            for L in limb_counts:
                if L > len(outputs): continue
                mask=(1<<(26*L))-1
                vhi=0
                vlo=0
                for j in range(L):
                    vhi=(vhi<<26)|outputs[j]
                    vlo |= outputs[j]<<(26*j)
                maxstart=len(outputs)-L+1
                for j in range(maxstart):
                    if "msf" in orders:
                        if vhi % p == target:
                            hits.append({"seed":seed,"mode":mode,"limbs":L,"order":"msf","start_output":j,"raw_integer":hex(vhi)})
                        counts[f"{mode}/{L}/msf"]+=1
                    if "lsf" in orders:
                        if vlo % p == target:
                            hits.append({"seed":seed,"mode":mode,"limbs":L,"order":"lsf","start_output":j,"raw_integer":hex(vlo)})
                        counts[f"{mode}/{L}/lsf"]+=1
                    if j+L < len(outputs):
                        vhi=((vhi<<26)&mask)|outputs[j+L]
                        vlo=(vlo>>26)|(outputs[j+L]<<(26*(L-1)))
                total+=maxstart*len(orders)
    return {"searched_seed_range":"0.."+str(seed_limit-1),"first_prng_outputs":prefix_draws,"26bit_modes":list(limb_modes),"limb_lengths":list(limb_counts),"limb_orders":list(orders),"checked_windows":total,"by_shape_counts":counts,"hits":hits,"elapsed_seconds":round(time.monotonic()-start,3),"boundary":"Only the specified FreeLIP 107-bit multiplicative recurrence, extraction modes, contiguous windows, limb orders and small integer seed range; not all historical generators, seeding mechanisms or encodings."}


def scan_lrand48_stream(curve, bytes_per_stream=150000, time_keys=("P-192","P-521","P-256","P-384","P-224")):
    targetx=curve["gx"].to_bytes((curve["p"].bit_length()+7)//8,"big")
    targety=curve["gy"].to_bytes((curve["p"].bit_length()+7)//8,"big")
    targets={"Gx_big":targetx,"Gx_little":targetx[::-1],"Gy_big":targety,"Gy_little":targety[::-1],"Gxy_uncompressed":b"\x04"+targetx+targety}
    out=[]
    for key in time_keys:
        when,_,_=PRIME_SEEDS[key]
        state=((unix(when)<<16)|0x330E)&LCG_MASK
        buffers={"top8":bytearray(),"top31_be":bytearray(),"top31_le":bytearray()}
        for i in range(bytes_per_stream):
            state=(LCG_A*state+LCG_C)&LCG_MASK
            buffers["top8"].append(state>>40)
            if i < bytes_per_stream//4:
                word=state>>17
                buffers["top31_be"].extend(word.to_bytes(4,"big"))
                buffers["top31_le"].extend(word.to_bytes(4,"little"))
        hits=[]
        for label,blob in buffers.items():
            for name,needle in targets.items():
                j=blob.find(needle)
                if j>=0: hits.append({"representation":label,"needle":name,"index":j})
        out.append({"seed_key":key,"timestamp":when,"byte_length_tested_per_representation":bytes_per_stream,"hits":hits})
    return {"runs":out,"boundary":"Only literal raw contiguous coordinate byte substrings of top8, top31_big/little streams, on given five historical seed timestamps; excludes hashing, scalar multiplication, rejection sampling and other clocks."}


def multiply(P,k,p,a):
    Q=None
    while k:
        if k&1:
            Q=point_add(Q,P,p,a)
        P=point_add(P,P,p,a)
        k>>=1
    return Q


def point_add(P,Q,p,a):
    if P is None: return Q
    if Q is None: return P
    x,y=P
    u,v=Q
    if x==u and (y+v)%p==0:
        return None
    if x==u and y==v:
        slope=((3*x*x+a)*pow(2*y,-1,p))%p
    else:
        slope=((v-y)*pow(u-x,-1,p))%p
    rx=(slope*slope-x-u)%p
    ry=(slope*(x-rx)-y)%p
    return rx,ry


def report(args):
    t0=time.monotonic()
    openssl=subprocess.check_output(["openssl","version"],text=True).strip()
    ctrl=[]
    for name,seed,p,b,gx,expected_tries in CALIBRATION:
        x,tries=zrandom_x(seed,p,b)
        ctrl.append({"name":name,"seed":seed,"tries":tries,"expected_tries":expected_tries,"match_x":x==gx and tries==expected_tries})
    assert all(c["match_x"] for c in ctrl)
    seed_ctrl=[]
    for key,(when,n,expected) in PRIME_SEEDS.items():
        got=lcg_candidate(unix(when),n,20,40,2)
        seed_ctrl.append({"name":key,"candidate":n,"match_seed":got==expected})
    for key,(when,n,expected) in BINARY_SEEDS.items():
        got=lcg_candidate(unix(when)//2,n,5,17,8)
        seed_ctrl.append({"name":key,"candidate":n,"match_seed":got==expected})
    assert all(x["match_seed"] for x in seed_ctrl)
    curve=parse_openssl_curve("prime256v1")
    assert curve["gx"] == 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296
    assert curve["a"]==curve["p"]-3
    assert multiply((curve["gx"],curve["gy"]),curve["n"],curve["p"],curve["a"]) is None
    cpp = Path(__file__).with_name("p256_scan_freelip.cpp")
    if not cpp.exists():
        raise FileNotFoundError("Expected p256_scan_freelip.cpp next to driver")
    scanner = Path(__file__).with_name("p256_scan_freelip")
    if not scanner.exists() or cpp.stat().st_mtime > scanner.stat().st_mtime:
        subprocess.run(["g++","-O3","-std=c++17","-o",str(scanner),str(cpp)],check=True)
    def scan(count,starts, optional_data=None):
        if optional_data:
            data=json.loads(Path(optional_data).read_text())
            assert data["seed_count"] == count and data["seed_start"] == starts
            assert data["first_prng_outputs"] == args.prefix_draws
        else:
            data=json.loads(subprocess.check_output([str(scanner), str(count), str(args.prefix_draws), hex(curve["gx"]), str(starts)],text=True))
        assert sum(data["shape_counts"]) == data["checked_windows"]
        return data
    scanned=scan(args.seed_limit,0,args.scanner_json)
    t=unix(PRIME_SEEDS["P-256"][0])
    timestamp_scanned=scan(172801,t-86400,args.timestamp_scanner_json)
    # Independent positive: derive a known output using Python, feed only its x-coordinate
    # to the unrelated compiled exhaustive scanner, and demand the exact seed and offset.
    seed=20000
    state=seed
    synthetic_outputs=[]
    for _ in range(25):
        state=state*A%M
        synthetic_outputs.append(state&MASK26)
    raw=0
    for limb in synthetic_outputs[7:18]:
        raw=(raw<<26)|limb
    synthetic_x=raw%curve["p"]
    test_scan=json.loads(subprocess.check_output([str(scanner),"20002","25",hex(synthetic_x),"0"],text=True))
    assert test_scan["hits"] == ["20000 low26 11 msf 7"],test_scan
    positive={"synthetic_target_x":hex(synthetic_x),"expected":"20000 low26 11 msf 7","actual_hits":test_scan["hits"],"pass":True}
    historical=CALIBRATION[1] # original prime239v1, second positive independent of P-256 input
    historical_scan=json.loads(subprocess.check_output([str(scanner),"20421","64",hex(historical[4]),"0",hex(historical[2])],text=True))
    assert historical_scan["hits"] == ["20420 low26 11 msf 29"],historical_scan
    historical_positive={"historical_curve":"prime239v1","historical_seed":20420,"published_target_x":hex(historical[4]),"expected":"20420 low26 11 msf 29","actual_hits":historical_scan["hits"],"pass":True}
    lrand=scan_lrand48_stream(curve,args.stream_bytes)
    cfg={"seed_limit":args.seed_limit,"prefix_draws":args.prefix_draws,"stream_bytes":args.stream_bytes}
    result={"title":"MathGraph P-256 base-point origin: post-source bounded forensics probe (not pre-registered, not blind)","asof_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"status":"CANDIDATE" if scanned["hits"] or timestamp_scanned["hits"] or any(row["hits"] for row in lrand["runs"]) else "NO_EXACT_MATCH_IN_DECLARED_GRAMMARS; GENERAL_ORIGIN_UNKNOWN","source":"https://www.anthropic.com/research/ecdsa-curve-origins","code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"source_openssl":openssl,"cpp_checker_sha256":hashlib.sha256(cpp.read_bytes()).hexdigest(),"cpp_binary_sha256":hashlib.sha256(scanner.read_bytes()).hexdigest(),"args":cfg,"calibration":{"freeLIP_basepoints":ctrl,"lrand48_seeds":seed_ctrl,"freeLIP_matches":sum(c["match_x"] for c in ctrl),"lrand48_matches":sum(c["match_seed"] for c in seed_ctrl)},"target":{"name":"NIST P-256 / prime256v1","gx":hex(curve["gx"]),"gy":hex(curve["gy"]),"curve_parameter_source":"openssl ecparam -name prime256v1 -param_enc explicit","curve_parameters_openssl_sha256":curve["openssl_sha256"],"on_curve":True,"order_n_check":True},"searches":{"freeLIP_small_seeds":scanned,"freeLIP_timestamp_window":timestamp_scanned,"historical_lrand48_raw_substring":lrand},"scanner_positive_control":positive,"scanner_historical_positive_control":historical_positive,"total_wall_seconds":round(time.monotonic()-t0,3),"epistemics":{"historical_generator":"UNKNOWN","general_cryptanalytic_success":"UNKNOWN","uniqueness":"NOT_CLAIMED","negative":"ONLY_WITHIN_EXACT_RECORDED_SEARCH_BOUNDS","strong_competitor":"NOT_RUN; this is an independent bounded negative/control probe, not an autonomous-development superiority test","private_keys":"NOT_ATTEMPTED"}}
    return result


def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--seed-limit",type=int,default=65536)
    pa.add_argument("--prefix-draws",type=int,default=192)
    pa.add_argument("--stream-bytes",type=int,default=150000)
    pa.add_argument("--out",default="/mnt/data/p256_origin_results.json")
    pa.add_argument("--scanner-json",default=None,help="Precomputed compiled small-seed scan JSON")
    pa.add_argument("--timestamp-scanner-json",default=None,help="Precomputed compiled timestamp scan JSON")
    args=pa.parse_args()
    r=report(args)
    Path(args.out).write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":r["status"],"calibration":{k:v for k,v in r["calibration"].items() if k.endswith("matches")},"freeLIP_windows":r["searches"]["freeLIP_small_seeds"]["checked_windows"]+r["searches"]["freeLIP_timestamp_window"]["checked_windows"],"freeLIP_hits":r["searches"]["freeLIP_small_seeds"]["hits"]+r["searches"]["freeLIP_timestamp_window"]["hits"],"lrand48_hits":sum(len(x["hits"]) for x in r["searches"]["historical_lrand48_raw_substring"]["runs"]),"time_s":r["total_wall_seconds"]},indent=2))

if __name__=="__main__":
    main()
