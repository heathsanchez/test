#!/usr/bin/env python3
"""Frozen claim-lineage experiment. Closed syntax, bounded native examples."""
import datetime,functools,hashlib,html,json,re,urllib.request
from html.parser import HTMLParser
from pathlib import Path

NEW="https://docs.python.org/3/library/functools.html"
EXPOSED="https://docs.python.org/3/library/bisect.html"
OUT=Path(__file__).with_name("result.json")
class Owners(HTMLParser):
    def __init__(self):
        super().__init__();self.entries=[];self.active=None;self.depth=0;self.parts=[];self.owner="";self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","nav"):self.skip+=1
        if self.skip:return
        if self.active is not None:self.depth+=1;return
        if tag in ("dt","dd"):self.active=tag;self.depth=0;self.parts=[]
    def handle_data(self,t):
        if not self.skip and self.active:self.parts.append(t)
    def handle_endtag(self,tag):
        if tag in ("script","style","nav"):self.skip=max(0,self.skip-1);return
        if self.skip or self.active is None:return
        if tag!=self.active and self.depth>0:self.depth-=1;return
        if tag!=self.active:return
        text=re.sub(r"\s+"," ",html.unescape(" ".join(self.parts))).strip()
        if self.active=="dt":self.owner=text
        elif self.active=="dd" and text:
            self.entries.append({"id":len(self.entries),"owner":self.owner,
                                 "body":text[:10000]})
        self.parts=[];self.active=None;self.depth=0
def canonical(x):return re.sub(r"\s+","",x.lower())
def owning(entries,method):
    # Exact terminal identifier followed by parenthesis, no mere mention from dd.
    pattern=r"(?<![a-z0-9_])"+re.escape(method.lower())+r"\("
    owners=[e for e in entries if re.search(pattern,canonical(e["owner"]))]
    return {"status":"OWNER_MATCH","entry":owners[0]} if len(owners)==1 else {
            "status":"UNKNOWN_OWNER_CARDINALITY","count":len(owners)}
def find_edge(description,target):
    # A tiny, predeclared syntactic RELATION grammar, not an LLM.
    # "Returns the same as lru_cache(maxsize=None)" is a structural dependency.
    t=canonical(description)
    ok=bool(re.search(r"(?:sameas|equivalentto)(?:functools\.)?"+re.escape(target.lower())+r"\(maxsize=none\)",t))
    return {"status":"EXPLICIT_EQUIVALENCE_EDGE" if ok else "UNKNOWN_NO_EQUIVALENCE_EDGE",
            "target":target,"argument":"maxsize=None" if ok else None}
def source_property(description):
    t=description.lower()
    no_evict=bool(re.search(r"\bnever\s+needs?\s+to\s+evict\b|\bwithout\s+evicting\b",t))
    unbounded=bool(re.search(r"\bunbounded\b|\bunlimited\b",t))
    return {"explicit_no_eviction":no_evict,"explicit_unbounded":unbounded,
            "source_warrant":no_evict or unbounded}
def acquire(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Metalogic-ClaimLineage-V10/1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read(3_000_001);got=r.geturl()
    if got!=url or len(raw)>3_000_000:raise ValueError("SOURCE_INTEGRITY_FAILURE")
    parser=Owners();parser.feed(raw.decode("utf-8"))
    return raw,parser.entries
def native():
    observations={}
    for name,deco in (("cache",functools.cache),("unbounded_lru",functools.lru_cache(maxsize=None))):
        calls={"n":0}
        def f(x):
            calls["n"]+=1
            return x*7+1
        wrapped=deco(f)
        originals=[wrapped(i) for i in range(33)]
        again=wrapped(0)
        observations[name]={"calls":calls["n"],"first_result":originals[0],
                            "repeat_result":again,"bounded_reuse":calls["n"]==33 and again==originals[0]}
    return {"tested_keys":33,"observations":observations,
            "pair_pass":all(x["bounded_reuse"] for x in observations.values())}
def conventional(entries):
    # Equally informed conventional signature lookup followed by direct text
    # read of the cache section; uses the same frozen native witness.
    match=[e for e in entries if re.search(r"\bcache\(",canonical(e["owner"]))]
    if len(match)!=1:return {"status":"UNKNOWN_OWNER"}
    body=match[0]["body"]
    eq=("same as" in body.lower() and "lru_cache" in body.lower())
    persistent=("never needs to evict" in body.lower() or "unbounded" in body.lower())
    return {"status":"CONVENTIONAL_READ","owner":match[0]["owner"],
            "equivalence_claim":eq,"persistence_claim":persistent,"native":native()}
def exposed_bisect():
    raw,entries=acquire(EXPOSED)
    p=owning(entries,"insort_left");q=owning(entries,"bisect_left")
    if p["status"]!="OWNER_MATCH" or q["status"]!="OWNER_MATCH":
        return {"status":"UNKNOWN_EXPOSED_CHAIN_OWNER","p":p["status"],"q":q["status"]}
    edge="bisect_left(" in canonical(p["entry"]["body"])
    content=q["entry"]["body"].lower()
    equal=("left" in content and ("equal" in content or "before" in content))
    return {"status":"EXPOSED_CHAIN_CHECKED" if edge else "UNKNOWN_NO_EDGE",
            "source_sha256":hashlib.sha256(raw).hexdigest(),
            "edge_found":edge,"equality_statement":equal,
            "owner_ids":[p["entry"]["id"],q["entry"]["id"]]}
def main():
    assert owning([{"owner":"functools.cache ( function )","body":"see cache"}],"cache")["status"]=="OWNER_MATCH"
    assert owning([{"owner":"functools.cached_property ( function )","body":"see cache()"}],"cache")["status"]!="OWNER_MATCH"
    assert find_edge("Returns the same as lru_cache(maxsize=None).","lru_cache")["status"]=="EXPLICIT_EQUIVALENCE_EDGE"
    exposed=exposed_bisect() # Already seen calibration; never considered prospective new.
    raw,entries=acquire(NEW)
    own=owning(entries,"cache")
    edge={"status":"UNKNOWN_NO_OWNER"};dependent={"status":"UNKNOWN_NO_EDGE"}
    supported={"source_warrant":False}
    if own["status"]=="OWNER_MATCH":
        edge=find_edge(own["entry"]["body"],"lru_cache")
        supported=source_property(own["entry"]["body"])
        if edge["status"]=="EXPLICIT_EQUIVALENCE_EDGE":
            dependent=owning(entries,"lru_cache")
    evidence=native()
    baseline=conventional(entries)
    authorized=own["status"]=="OWNER_MATCH" and edge["status"]=="EXPLICIT_EQUIVALENCE_EDGE" and dependent["status"]=="OWNER_MATCH"
    if not authorized:verdict="UNKNOWN_DEPENDENCY_NOT_CLOSED"
    elif not supported["source_warrant"]:verdict="UNKNOWN_SOURCE_PROPERTY_NOT_WARRANTED"
    elif not evidence["pair_pass"]:verdict="REJECTED_NATIVE_COUNTEREXAMPLE"
    else:verdict="WARRANTED_BOUNDED_SOURCE_CHAIN_AND_NATIVE_REUSE"
    report={"source_url":NEW,"source_sha256":hashlib.sha256(raw).hexdigest(),
      "retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "source_owner_count":len(entries),"exposed_bisect":exposed,"owner":own,
      "edge":edge,"referenced_owner":dependent,"source_property":supported,
      "native":evidence,"conventional_baseline":baseline,
      "authority_withdrawal":{"equivalence_claim":"UNKNOWN_WITHDRAWN",
         "dependent_no_eviction_source_claim":"UNKNOWN_WITHDRAWN",
         "native_observations":"UNCHANGED"},
      "verdict":verdict,
      "limitations":["human-authored same-as relation grammar, anticipated Python operations",
        "bounded 33-key example cannot prove universal non-eviction",
        "baseline same source and methods, no timed human study",
        "operation count does not measure total engineering cost",
        "R7.2 CLC MathGraph remain unchanged and not called"]}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"verdict":verdict,"owner":own.get("status"),
      "edge":edge,"dependent":dependent.get("status"),
      "source_property":supported,"native":evidence,"baseline":baseline.get("status"),
      "exposed":exposed.get("status"),"source_sha256":report["source_sha256"]},sort_keys=True))
    if verdict=="REJECTED_NATIVE_COUNTEREXAMPLE":raise AssertionError("Native counterexample")
if __name__=="__main__":main()
