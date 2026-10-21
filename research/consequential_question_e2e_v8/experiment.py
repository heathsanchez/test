#!/usr/bin/env python3
"""Precommitted bounded source-question -> witness -> warrant experiment."""
import datetime, hashlib, heapq, html, json, re, urllib.request
from html.parser import HTMLParser
from pathlib import Path
URL="https://docs.python.org/3/library/heapq.html"
QUESTION="When heapq.heappop is called on a heap, which priority element does it remove and return?"
INPUTS=((7,1,4),(11,3,8))
OUT=Path(__file__).with_name("result.json")

class Blocks(HTMLParser):
    def __init__(self):
        super().__init__();self.blocks=[];self.buffer=[];self.active=False;self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","nav"):self.skip+=1
        if not self.skip and tag in ("p","dd","li") and not self.active:
            self.active=True;self.buffer=[]
    def handle_data(self,data):
        if self.active and not self.skip:self.buffer.append(data)
    def handle_endtag(self,tag):
        if tag in ("script","style","nav"):self.skip=max(0,self.skip-1)
        if tag in ("p","dd","li") and self.active and not self.skip:
            value=re.sub(r"\s+"," ",html.unescape(" ".join(self.buffer))).strip()
            if value:self.blocks.append(value)
            self.active=False;self.buffer=[]

def source():
    req=urllib.request.Request(URL,headers={"User-Agent":"Metalogic-CQ-V8-Research/1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read(3_000_001);redirect=r.geturl()
    if redirect!=URL or len(raw)>3_000_000:raise RuntimeError("SOURCE_IDENTITY")
    blocks=Blocks();blocks.feed(raw.decode("utf-8"))
    return raw,blocks.blocks

def compile_question(blocks):
    seen=[]
    for i,text in enumerate(blocks):
        lower=text.lower()
        if not re.search(r"\bheappop\b",lower):continue
        if not re.search(r"\b(?:pop|remove|return|retrieve)\w*\b",lower):continue
        has_min=bool(re.search(r"\bsmallest\b|\bminimum\b",lower))
        has_max=bool(re.search(r"\blargest\b|\bmaximum\b",lower))
        if has_min==has_max:continue
        seen.append({"block_index":i,"clause":text[:1000],"extreme":"smallest" if has_min else "largest"})
    return seen[0] if seen else None

def native_case(values):
    heap=list(values)
    heapq.heapify(heap)
    return heapq.heappop(heap),tuple(heap)

def candidate_observation(clause):
    if clause is None:return {"status":"UNKNOWN_NO_SOURCE_OBLIGATION"}
    outcome=[]
    for values in INPUTS:
        observed,post=native_case(values)
        expected=min(values) if clause["extreme"]=="smallest" else max(values)
        outcome.append({"input":list(values),"expected":expected,"observed":observed,
                        "pass":observed==expected,"original_unchanged":values in INPUTS})
    return {"status":"NATIVE_WITNESS_CHECKED","cases":outcome,
            "all_pass":all(x["pass"] for x in outcome),"native_calls":4}

def conventional_baseline(blocks):
    # Independent simple document lookup; same page, same admissible primitive calls.
    text=" ".join(blocks).lower()
    ix=text.find("heappop")
    local=text[max(0,ix-200):ix+600] if ix>=0 else ""
    if ix<0:return {"status":"UNKNOWN_NO_METHOD"}
    if "smallest" not in local and "largest" not in local:
        return {"status":"UNKNOWN_NO_LOCAL_SEMANTICS"}
    extreme="smallest" if "smallest" in local else "largest"
    observed=[native_case(x)[0] for x in INPUTS]
    expected=[min(x) if extreme=="smallest" else max(x) for x in INPUTS]
    return {"status":"NATIVE_CHECKED","extreme":extreme,
            "cases":2,"pass":observed==expected,"native_calls":4}

def main():
    raw,blocks=source()
    selected=compile_question(blocks)
    candidate=candidate_observation(selected)
    baseline=conventional_baseline(blocks)
    # Native observations by themselves cannot establish the source meaning.
    withdrawal="UNKNOWN_SOURCE_AUTHORITY_REVOKED"
    restored=selected is not None and candidate.get("all_pass",False)
    verdict=("UNKNOWN_SOURCE_OBLIGATION" if selected is None else
             "REJECTED_NATIVE_MISMATCH" if not candidate.get("all_pass") else
             "WARRANTED_BOUNDED_TWO_INPUT_NATIVE_CORRESPONDENCE")
    comparison=("TIE_ON_TWO_NATIVE_RESULTS" if baseline.get("pass") is True and restored
                else "COMPARATOR_UNKNOWN_OR_DIFFERENT")
    result={"url":URL,"source_sha256":hashlib.sha256(raw).hexdigest(),
      "source_bytes":len(raw),"retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "question":QUESTION,"blocks":len(blocks),"selected_source_span":selected,
      "compiled_native_witness":candidate,"full_info_native_baseline":baseline,
      "comparison":comparison,"withdrawal":withdrawal,"restoration":restored,
      "independent_claim":"unrelated observation not invalidated by withdrawing this source",
      "verdict":verdict,"limitations":["selection grammar and min/max semantics preprogrammed",
         "baseline does not represent blinded human work",
         "2 finite test inputs do not prove universally correct API semantics",
         "R7.2, CLC, MathGraph Check unchanged but not invoked"]}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"verdict":verdict,"selected":selected,"candidate":candidate,
        "baseline":baseline,"comparison":comparison,"source_sha256":result["source_sha256"]},sort_keys=True))
    if verdict=="REJECTED_NATIVE_MISMATCH":raise AssertionError("NATIVE_MISMATCH")
if __name__=="__main__":main()
