#!/usr/bin/env python3
"""V7 frozen source-location research. Not natural-language entailment."""
import collections, datetime, hashlib, html, json, math, re, urllib.request
from html.parser import HTMLParser
from pathlib import Path

URL="https://docs.python.org/3/library/collections.html"
QUESTION="When assigning a key through collections.ChainMap, which underlying mapping receives the assignment?"
ANCHOR=QUESTION.split("collections.")[1].split(",")[0].split(" ")[0]
OUT=Path(__file__).with_name("result.json")
STOP={"when","which","through","the","a","an","of","to","in","does","is","do","key","receives"}
SYNS={
 "assign":{"assign","assignment","assigned","setting","set","writes","write","writing","update","updates","updated"},
 "mapping":{"mapping","mappings","map","maps","dict","dictionary","dictionaries"},
}
def words(text):
    return set(re.findall(r"[a-z]+",text.lower()))-STOP
def concepts(text):
    w=words(text)
    return {k for k,values in SYNS.items() if w & values}

class Blocks(HTMLParser):
    def __init__(self):
        super().__init__(); self.blocks=[]; self.stack=[];self.parts=[];self.current=None
        self.heading="";self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","nav"):self.skip+=1
        if self.skip:return
        if tag in ("h1","h2","h3"):
            self.current=("heading",tag);self.parts=[]
        elif tag in ("p","li","dd") and self.current is None:
            self.current=("block",tag);self.parts=[]
    def handle_data(self,data):
        if not self.skip and self.current:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag in ("script","style","nav"):
            self.skip=max(0,self.skip-1);return
        if self.skip or not self.current or self.current[1]!=tag:return
        text=re.sub(r"\s+"," ",html.unescape(" ".join(self.parts))).strip()
        kind,_=self.current
        if kind=="heading" and text:self.heading=text
        elif kind=="block" and text and len(text)>30:
            self.blocks.append({"index":len(self.blocks),"heading":self.heading,"text":text})
        self.current=None;self.parts=[]
def read_source():
    request=urllib.request.Request(URL,headers={"User-Agent":"Metalogic-SourceFidelity-V7/1"})
    with urllib.request.urlopen(request,timeout=30) as response:
        data=response.read(3_000_001);destination=response.geturl()
    if destination!=URL or len(data)>3_000_000:raise RuntimeError("SOURCE_INTEGRITY_FAILURE")
    parser=Blocks();parser.feed(data.decode("utf-8"))
    return data,parser.blocks
def candidate_score(block):
    text=block["text"];heading=block["heading"]
    c=concepts(text)
    qwords=words(QUESTION)
    overlap=len(words(text)&qwords)
    anchor_present=ANCHOR.lower() in (text+" "+heading).lower()
    # This does not pre-encode "first mapping" as desired answer.
    return overlap+4*("assign" in c)+3*("mapping" in c)+2*anchor_present
def bm25_baseline(blocks):
    q=words(QUESTION);docs=[words(b["text"]+" "+b["heading"]) for b in blocks]
    df={x:sum(x in row for row in docs) for x in q}
    N=len(docs)
    def score(i):
        doc=docs[i]
        return sum(math.log(1+(N-df[x]+0.5)/(df[x]+0.5)) for x in q if x in doc)
    best=sorted(range(N),key=lambda i:(-score(i),i))[0] if N else None
    return {"selected":blocks[best] if best is not None else None,
            "score":score(best) if best is not None else None}
def select(blocks):
    eligible=[b for b in blocks if ANCHOR.lower() in (b["heading"]+" "+b["text"]).lower()]
    if not eligible:return {"status":"UNKNOWN_NO_ANCHORED_SOURCE"}
    ranked=sorted(eligible,key=lambda b:(-candidate_score(b),b["index"]))
    b=ranked[0]
    if candidate_score(b)<7:return {"status":"UNKNOWN_INSUFFICIENT_TARGET_SIGNAL","score":candidate_score(b)}
    return {"status":"SOURCE_SPAN_CANDIDATE","selected":b,"score":candidate_score(b)}
def reference_adequacy(block):
    if block is None:return {"status":"UNKNOWN_NO_SOURCE_SPAN"}
    text=block["text"].lower()
    # Deliberately source-specific EVALUATION predicate, not part of candidate selector.
    mentions_first=("first mapping" in text or "first map" in text)
    mentions_write=any(x in text for x in ("write","writes","updat","assign","setting"))
    return {"status":"SOURCE_TEXT_SUPPORTS_TARGET" if mentions_first and mentions_write
            else "REJECTED_TARGET_MISS","mentions_first":mentions_first,"mentions_write":mentions_write}
def native_behavior():
    first={"original":1};second={"original":2}
    chain=collections.ChainMap(first,second)
    chain["fresh"]=9
    result={"first_contains":first.get("fresh"),"second_contains":second.get("fresh"),
            "read_preserves_other":chain["original"]==1}
    assert result=={"first_contains":9,"second_contains":None,"read_preserves_other":True}
    return result
def main():
    # Exposed local invariants, no real source inspected here.
    assert "assign" in concepts("writes updates")
    assert "mapping" in concepts("underlying mappings")
    assert reference_adequacy({"text":"ChainMap allows many lookups."})["status"]=="REJECTED_TARGET_MISS"
    data,blocks=read_source()
    candidate=select(blocks)
    baseline=bm25_baseline(blocks)
    result=reference_adequacy(candidate.get("selected"))
    base_ref=reference_adequacy(baseline.get("selected"))
    native=native_behavior()
    if candidate["status"]!="SOURCE_SPAN_CANDIDATE":
        verdict="UNKNOWN_INAPPLICABLE"
    elif result["status"]!="SOURCE_TEXT_SUPPORTS_TARGET":
        verdict="REJECTED_SOURCE_TO_QUESTION_FIDELITY"
    else:
        verdict="WARRANTED_BOUNDED_SOURCE_SPAN_RETRIEVAL"
    report={
      "source_url":URL,"source_sha256":hashlib.sha256(data).hexdigest(),
      "retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "question":QUESTION,"anchor":ANCHOR,"block_count":len(blocks),
      "candidate":candidate,"reference_adequacy":result,
      "bm25_equal_source_baseline":baseline,"baseline_reference_adequacy":base_ref,
      "independent_native_chainmap":native,"verdict":verdict,
      "assessment_limitations":[
        "source-specific posthoc-style reference predicate was predeclared, not independent blinded human review",
        "BM25 is algorithmic baseline, not skilled conventional engineer",
        "candidate does not infer which mapping without reading/semantic interpretation of selected span",
        "no source-to-native witness synthesis, no economic cost comparison",
        "R7.2 CLC MathGraph existing interfaces unmodified and not invoked"
      ]
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"verdict":verdict,"candidate":candidate,
      "adequacy":result,"baseline_adequacy":base_ref,
      "native":native,"source_sha256":report["source_sha256"]},sort_keys=True))
if __name__=="__main__":main()
