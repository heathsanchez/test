#!/usr/bin/env python3
"""Precommitted cross-source documentation-owner gate; independent native baseline."""
import bisect, datetime, hashlib, html, json, re, urllib.request
from html.parser import HTMLParser
from pathlib import Path

URL="https://docs.python.org/3/library/bisect.html"
TARGET="bisect.insort_left"
QUESTION="When bisect.insort_left inserts an item into a sorted list, is the item inserted to the left of equal values?"
OUT=Path(__file__).with_name("result.json")

class DefinitionBlocks(HTMLParser):
    def __init__(self):
        super().__init__();self.scope=None;self.depth=0;self.parts=[];self.signature=None
        self.entries=[];self.prose=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style"):self.skip+=1
        if self.skip:return
        if self.scope is not None:
            self.depth+=1;return
        if tag in ("dt","dd","p"):
            self.scope=tag;self.depth=0;self.parts=[]
    def handle_data(self,data):
        if not self.skip and self.scope is not None:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag in ("script","style"):self.skip=max(0,self.skip-1);return
        if self.skip or self.scope is None:return
        if tag!=self.scope and self.depth>0:
            self.depth-=1;return
        if tag!=self.scope:return
        text=re.sub(r"\s+"," ",html.unescape(" ".join(self.parts))).strip()
        if self.scope=="dt":self.signature=text
        elif self.scope=="dd" and text:
            self.entries.append({"index":len(self.entries),"owner_signature":self.signature or "",
                                 "description":text[:5000]})
        elif self.scope=="p" and text:
            self.prose.append({"index":len(self.prose),"text":text[:5000]})
        self.scope=None;self.parts=[];self.depth=0

def exact_identity(entries):
    token=TARGET.rsplit(".",1)[-1]
    matches=[e for e in entries if re.search(r"(?<![A-Za-z0-9_])"+re.escape(token)+r"\s*\(",e["owner_signature"])]
    if len(matches)==0:return {"status":"UNKNOWN_NO_EXACT_OWNER","count":0}
    if len(matches)!=1:return {"status":"UNKNOWN_AMBIGUOUS_OWNER","count":len(matches)}
    return {"status":"SOURCE_OWNER_MATCH","definition":matches[0],"count":1}
def strong_conventional(entries):
    # Independently implemented exact-signature lookup, same information.
    candidates=[e for e in entries if "insort_left(" in e["owner_signature"]]
    return {"status":"SOURCE_OWNER_MATCH" if len(candidates)==1 else "UNKNOWN",
            "definition":candidates[0] if len(candidates)==1 else None,
            "count":len(candidates)}
def naive(prose):
    terms=("bisect","insort_left","insert","equal","left")
    ranked=sorted(prose,key=lambda e:(-sum(k in e["text"].lower() for k in terms),e["index"]))
    return ranked[0] if ranked else None
class Item:
    def __init__(self,key,tag):self.key=key;self.tag=tag
    def __lt__(self,other):return self.key<other.key
def native_baseline():
    existing=[Item(1,"lower"),Item(2,"old-a"),Item(2,"old-b"),Item(3,"upper")]
    inserted=Item(2,"new")
    bisect.insort_left(existing,inserted)
    labels=[e.tag for e in existing]
    return {"labels":labels,"left_of_equal":labels==["lower","new","old-a","old-b","upper"],
            "native_insort_calls":1}
def main():
    # Pre-source synthetic controls distinguish the owning definition from mere mention.
    fixtures=[{"owner_signature":"bisect.insort_right(a, x)","description":"See insort_left(a,x) for comparison."},
              {"owner_signature":"bisect.insort_left(a, x)","description":"Inserts x to the left."}]
    assert exact_identity(fixtures)["definition"]["owner_signature"]=="bisect.insort_left(a, x)"
    assert exact_identity(fixtures[:1])["status"]=="UNKNOWN_NO_EXACT_OWNER"
    request=urllib.request.Request(URL,headers={"User-Agent":"Metalogic-V9-SourceIdentity/1"})
    with urllib.request.urlopen(request,timeout=30) as response:
        raw=response.read(3_000_001);destination=response.geturl()
    if len(raw)>3_000_000 or destination!=URL:raise RuntimeError("SOURCE_INTEGRITY")
    parsed=DefinitionBlocks();parsed.feed(raw.decode("utf-8"))
    proposed=exact_identity(parsed.entries)
    conventional=strong_conventional(parsed.entries)
    lexical=naive(parsed.prose)
    native=native_baseline()
    # Unambiguous operation ownership is distinct from entailment of "left of equal".
    if proposed["status"]!="SOURCE_OWNER_MATCH":verdict="UNKNOWN_SOURCE_OWNER"
    elif conventional["status"]!="SOURCE_OWNER_MATCH":verdict="UNKNOWN_COMPARATOR_OWNER"
    elif proposed["definition"]["owner_signature"]!=conventional["definition"]["owner_signature"]:
        verdict="REJECTED_OWNER_MISMATCH"
    else:verdict="WARRANTED_BOUNDED_OPERATION_IDENTITY"
    selected_text=proposed.get("definition",{}).get("description","")
    # Independent postselection relevance check is a heuristic only.
    mentions_left="left" in selected_text.lower()
    mentions_equal=("equal" in selected_text.lower() or "existing" in selected_text.lower())
    report={
      "source_url":URL,"source_sha256":hashlib.sha256(raw).hexdigest(),
      "retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "target":TARGET,"question":QUESTION,"definitions":len(parsed.entries),"prose_blocks":len(parsed.prose),
      "candidate":proposed,"conventional_signature_baseline":conventional,
      "naive_lexical_baseline":lexical,"native_baseline":native,
      "owner_semantic_indicators":{"left":mentions_left,"equal_or_existing":mentions_equal},
      "source_claim_entailed":"UNKNOWN_UNTIL_INDEPENDENT_SEMANTIC_ADJUDICATION",
      "native_witness_compiled_from_source":False,"verdict":verdict,
      "comparative_claim":"TIE_WITH_SIGNATURE_AWARE_BASELINE_IF_BOTH_MATCH",
      "limits":["not a blinded expert", "Python documentation ownership is a predefined markup grammar",
                "native probe preprogrammed, not compiled from source", "R7.2 CLC MathGraph unchanged and uninvoked"]
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"source_sha256":report["source_sha256"],"verdict":verdict,
      "proposed":proposed,"conventional":conventional,"lexical":lexical,
      "native":native,"indicators":report["owner_semantic_indicators"]},sort_keys=True))
if __name__=="__main__":main()
